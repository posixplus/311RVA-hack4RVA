import express from 'express'
import cors from 'cors'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import pdfParse from 'pdf-parse'
import OpenAI from 'openai'
import dotenv from 'dotenv'

dotenv.config()

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const DOCS_DIR = path.join(__dirname, '../docs/richmond-manuals')
const CHUNK_SIZE = 600   // characters per chunk
const CHUNK_OVERLAP = 80 // overlap between chunks
const TOP_K = 8          // chunks to inject into prompt

// ── Document loading & chunking ──────────────────────────────────────────────
let chunks = []  // { text, source }

async function loadDocs() {
  if (!fs.existsSync(DOCS_DIR)) {
    console.warn(`⚠️  Docs directory not found: ${DOCS_DIR}`)
    console.warn('   Place Richmond PDF files in docs/richmond-manuals/')
    return
  }
  const files = fs.readdirSync(DOCS_DIR).filter(f => f.toLowerCase().endsWith('.pdf'))
  if (files.length === 0) {
    console.warn('⚠️  No PDFs found in docs/richmond-manuals/ — responses will be general only')
    return
  }
  for (const file of files) {
    try {
      const buffer = fs.readFileSync(path.join(DOCS_DIR, file))
      const data = await pdfParse(buffer)
      let text = data.text
        .replace(/\s+/g, ' ')                          // collapse whitespace
        .replace(/([a-zA-Z])(\d{3,})/g, '$1 $2')      // "Line741741" → "Line 741741"
        .replace(/(\d{3,})([a-zA-Z])/g, '$1 $2')      // "7233text" → "7233 text"
        .replace(/ContactNumber/gi, 'Contact | Number') // fix merged table headers
        .trim()
      // Slide a window across the text
      for (let i = 0; i < text.length; i += CHUNK_SIZE - CHUNK_OVERLAP) {
        const chunk = text.slice(i, i + CHUNK_SIZE)
        if (chunk.trim().length > 50) chunks.push({ text: chunk, source: file })
      }
      console.log(`  ✓ ${file} → ${Math.ceil(text.length / (CHUNK_SIZE - CHUNK_OVERLAP))} chunks`)
    } catch (err) {
      console.error(`  ✗ Failed to parse ${file}:`, err.message)
    }
  }
  console.log(`\n📚 Loaded ${chunks.length} chunks from ${files.length} PDFs\n`)
}

// ── PII redaction (Privacy-by-Design) ────────────────────────────────────────
// Strips names, addresses, and other PII before sending to external LLM API
// and before retrieval scoring (so personal nouns don't dilute keyword matches)
function redactPII(text) {
  return text
    .replace(/\bmy name is\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)*/gi, 'my name is [REDACTED]')
    .replace(/\bi am\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)*\b(?!\s+(years|months|old|\d))/g, 'I am [REDACTED]')
    .replace(/\b\d+\s+[A-Z][a-zA-Z\s]*(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Blvd|Boulevard|Court|Ct|Way|Place|Pl)\b/gi, '[ADDRESS REDACTED]')
    .replace(/\b[A-Z][a-z]+\s+[A-Z][a-z]+(?=\s+(here|is|was|has|had|said|told|called))/g, '[NAME REDACTED]')
    .replace(/\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b/g, '[SSN REDACTED]')  // SSN pattern
    .replace(/\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b/g, '[PHONE REDACTED]') // phone pattern
}

// ── Simple keyword retrieval (TF-IDF-ish scoring) ────────────────────────────
function tokenize(text) {
  return text.toLowerCase().match(/\b\w{3,}\b/g) || []
}

// Stop words to ignore in scoring
const STOP = new Set(['the','and','for','are','was','that','this','with','have',
  'from','they','been','not','but','you','your','our','can','may','will','also',
  'more','their','when','which','there','about','what','said','para','que','con',
  'los','las','una','como','por','del','los','sus','más','sin','ser','han'])

function scoreChunk(queryTokens, chunk) {
  const cTokens = tokenize(chunk.text)
  const cSet = new Map()
  for (const t of cTokens) cSet.set(t, (cSet.get(t) || 0) + 1)
  let hits = 0
  for (const qt of queryTokens) {
    if (!STOP.has(qt) && cSet.has(qt)) hits += cSet.get(qt)
  }
  return hits / (cTokens.length || 1)
}

function retrieve(query) {
  const queryTokens = tokenize(query).filter(t => !STOP.has(t))
  if (queryTokens.length === 0 || chunks.length === 0) return []
  return chunks
    .map(c => ({ ...c, score: scoreChunk(queryTokens, c) }))
    .filter(c => c.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, TOP_K)
}

// ── Express app ───────────────────────────────────────────────────────────────
const app = express()
app.use(cors())
app.use(express.json())

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', chunks: chunks.length, docs_dir: DOCS_DIR })
})

// Debug endpoint — see exactly what chunks a query retrieves
// Usage: POST http://localhost:3001/debug  { "query": "SNAP work requirements age" }
app.post('/debug', (req, res) => {
  const { query } = req.body
  if (!query) return res.status(400).json({ error: 'query required' })
  const results = retrieve(query)
  res.json({
    query,
    chunks_found: results.length,
    results: results.map(c => ({ source: c.source, score: c.score, preview: c.text.slice(0, 300) }))
  })
})

app.post('/chat', async (req, res) => {
  const { message, lang = 'en', history = [] } = req.body
  if (!message) return res.status(400).json({ error: 'message is required' })

  if (!process.env.FEATHERLESS_API_KEY) {
    return res.status(500).json({ error: 'FEATHERLESS_API_KEY not set in local-server/.env' })
  }

  // Privacy-by-Design: redact PII before retrieval AND before sending to external API
  const safeMessage = redactPII(message)
  const safeHistory = history.slice(-6).map(m => ({ role: m.role, content: redactPII(m.content || '') }))

  // RAG: find relevant chunks using the PII-stripped query
  const topChunks = retrieve(safeMessage)
  const context = topChunks.length
    ? topChunks.map(c => `[Source: ${c.source}]\n${c.text}`).join('\n\n---\n\n')
    : ''

  const systemPrompt = lang === 'es'
    ? `Eres un asistente de recursos comunitarios para la ciudad de Richmond, Virginia.
Responde SIEMPRE en español. Sé conciso (2-4 oraciones), claro y empático.

REGLAS CRÍTICAS:
1. Usa el CONTEXTO a continuación como única fuente de verdad para todos los datos específicos — edades, fechas, montos, plazos.
2. PUEDES aplicar razonamiento lógico simple al contexto (ej: si el documento dice "64 años o menos deben cumplir requisitos" y el usuario tiene 60, concluye que SÍ debe cumplirlos — porque 60 es menor que 64).
3. NUNCA sustituyas tu conocimiento de entrenamiento por números o detalles de política que están en el contexto. El contexto es más actualizado.
4. Comparte TODA la orientación relevante del contexto aunque solo responda parcialmente la pregunta. Por ejemplo, si alguien pregunta por direcciones de refugios pero el contexto tiene consejos de seguridad para apagones, comparte esos consejos Y señala que para ubicaciones específicas deben llamar al 311 o sintonizar las noticias locales.
5. Solo di "No tengo esa información" si el contexto no tiene absolutamente nada relacionado con el tema.

CONTEXTO DE DOCUMENTOS MUNICIPALES DE RICHMOND:
${context || 'No se encontraron documentos relevantes. Indica que no tienes esa información.'}`
    : `You are a community resource assistant for Richmond, Virginia.
Be concise (2-4 sentences), clear, and empathetic. Always respond in English.

CRITICAL RULES:
1. Use the CONTEXT below as your sole source of truth for all specific facts — ages, dates, dollar amounts, deadlines, thresholds.
2. You MAY apply simple logical reasoning to the context (e.g., if the document says "64 or under are required" and the user is 60, conclude that YES, they are required — since 60 is under 64).
3. NEVER substitute your training knowledge for numbers or policy details that are in the context. The context is more up-to-date.
4. Share ALL relevant guidance from the context even if it only partially answers the question. For example, if someone asks about warming shelter addresses but the context has safety tips for power outages, share those tips AND note that for specific shelter locations they should call 311 or tune to local news.
5. Only say "I don't have that specific information" if the context has absolutely nothing related to the topic.

CONTEXT FROM RICHMOND MUNICIPAL DOCUMENTS:
${context || 'No relevant documents found. Tell the user you do not have that specific information.'}`

  try {
    const client = new OpenAI({
      apiKey: process.env.FEATHERLESS_API_KEY,
      baseURL: 'https://api.featherless.ai/v1',
    })
    const model = process.env.FEATHERLESS_MODEL || 'NousResearch/Meta-Llama-3.1-8B-Instruct'
    const messages = [
      { role: 'system', content: systemPrompt },
      ...safeHistory,
      { role: 'user', content: safeMessage },
    ]

    const completion = await client.chat.completions.create({
      model,
      messages,
      max_tokens: 512,
      temperature: 0.1,
    })

    res.json({ response: completion.choices[0].message.content })
  } catch (err) {
    console.error('Featherless API error:', err.message)
    res.status(502).json({ error: 'Groq API error: ' + err.message })
  }
})

// ── Start ─────────────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3001
loadDocs().then(() => {
  app.listen(PORT, () => {
    console.log(`🚀 Richmond local server running at http://localhost:${PORT}`)
    console.log(`   POST http://localhost:${PORT}/chat  — send { message, lang, history }`)
    console.log(`   GET  http://localhost:${PORT}/health — check status\n`)
  })
})
