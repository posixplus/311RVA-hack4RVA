# Running Locally with Groq (No AWS Required)

This lets you demo the full app — real LLM responses grounded in Richmond PDFs — without deploying anything to AWS.

## How It Works

```
Browser (website/)  →  local-server/server.js  →  Groq API (cloud)
                              ↑
                    docs/richmond-manuals/*.pdf
                    (loaded at startup, chunked for RAG)
```

The local server loads all PDFs at startup, chunks them, and does keyword-based retrieval to find the most relevant passages for each question. Those passages are injected into the Groq prompt as context.

---

## Setup (3 steps)

### 1. Add your Groq API key

Edit `local-server/.env`:
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
```
Get a free key (no credit card needed) at https://console.groq.com/keys

### 2. Make sure your PDFs are in place

```
docs/richmond-manuals/
├── SNAP_Work_Requirements_flyer.pdf
├── Staying_Safe_During_Freezing_Temperatures.pdf
├── KYR-Encounter-ICE-Nov.-2024-English.pdf
└── ... (all 10 PDFs)
```

The server loads these automatically. You can add more PDFs at any time — just restart the server.

### 3. Start both servers

```bash
./scripts/start-local.sh
```

Then open http://localhost:5173 in your browser.

---

## Manual Start (if you prefer two terminals)

**Terminal 1 — Local RAG server:**
```bash
cd local-server
npm install   # first time only
npm start
# → Running at http://localhost:3001
# → Loaded N chunks from 10 PDFs
```

**Terminal 2 — Website:**
```bash
cd website
# Make sure website/.env has: VITE_MODE=groq
npm run dev
# → http://localhost:5173
```

---

## Switching Modes

Edit `website/.env` and restart `npm run dev`:

| Mode | Setting | Description |
|------|---------|-------------|
| Demo | `VITE_MODE=demo` | Offline keyword responses, no API needed |
| Groq | `VITE_MODE=groq` | Real LLM via local server + Groq API |
| AWS  | `VITE_MODE=aws` + `VITE_API_ENDPOINT=...` | Deployed Bedrock + API Gateway |

The header badge shows the current mode: 🟡 DEMO · 🟢 GROQ · 🔴 LIVE

---

## Model Used

The local server uses `llama-3.1-8b-instant` on Groq — fast, free tier available, good for demos.
To change the model, edit the `model` field in `local-server/server.js`.
Other good options: `llama-3.3-70b-versatile`, `mixtral-8x7b-32768`.

---

## Troubleshooting

**"GROQ_API_KEY not set"** — Check that `local-server/.env` has your real key (not the placeholder).

**"No PDFs found"** — Make sure PDFs are in `docs/richmond-manuals/` (not a subdirectory).

**CORS error in browser** — Make sure the local server is running on port 3001 (`curl http://localhost:3001/health` should return `{"status":"ok",...}`).

**Port 3001 in use** — Set `PORT=3002` in `local-server/.env` and `VITE_GROQ_SERVER=http://localhost:3002` in `website/.env`.
