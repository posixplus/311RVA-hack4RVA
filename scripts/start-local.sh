#!/bin/bash
# ── Richmond Safety Net — Local Groq Mode Startup ─────────────────────────────
# Starts the local RAG server + the Vite dev server in two terminal tabs.
# Requires: Node.js 18+, your Groq API key in local-server/.env

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# ── 1. Check for Groq API key ─────────────────────────────────────────────────
if [ ! -f "$ROOT/local-server/.env" ]; then
  echo "⚠️  No local-server/.env found. Creating from template..."
  cp "$ROOT/local-server/.env.example" "$ROOT/local-server/.env"
  echo ""
  echo "👉 Open local-server/.env and paste your Groq API key, then re-run this script."
  echo "   Get a free key at: https://console.groq.com/keys"
  exit 1
fi

if grep -q "your_featherless_api_key_here" "$ROOT/local-server/.env"; then
  echo "❌ Please replace 'your_featherless_api_key_here' in local-server/.env with your real Featherless API key."
  echo "   Get a key at: https://featherless.ai"
  exit 1
fi

# ── 2. Install local-server dependencies if needed ────────────────────────────
if [ ! -d "$ROOT/local-server/node_modules" ]; then
  echo "📦 Installing local-server dependencies..."
  cd "$ROOT/local-server" && npm install
fi

# ── 3. Install website dependencies if needed ─────────────────────────────────
if [ ! -d "$ROOT/website/node_modules" ]; then
  echo "📦 Installing website dependencies..."
  cd "$ROOT/website" && npm install
fi

# ── 4. Set website to Groq mode ───────────────────────────────────────────────
if grep -q "^VITE_MODE=groq" "$ROOT/website/.env" 2>/dev/null; then
  echo "✅ Website already set to Groq mode"
else
  echo "⚙️  Setting VITE_MODE=groq in website/.env"
  sed -i '' 's/^VITE_MODE=.*/VITE_MODE=groq/' "$ROOT/website/.env" 2>/dev/null || \
    echo "VITE_MODE=groq" >> "$ROOT/website/.env"
fi

# ── 5. Start both servers ─────────────────────────────────────────────────────
echo ""
echo "🚀 Starting local Groq server on http://localhost:3001 ..."
cd "$ROOT/local-server" && node server.js &
GROQ_PID=$!

sleep 1

echo "🌐 Starting Vite dev server on http://localhost:5173 ..."
cd "$ROOT/website" && npm run dev &
VITE_PID=$!

echo ""
echo "────────────────────────────────────────────────────────"
echo "  Richmond Safety Net — Groq Mode"
echo "  Local RAG server : http://localhost:3001"
echo "  Website          : http://localhost:5173"
echo "────────────────────────────────────────────────────────"
echo "  Press Ctrl+C to stop both servers"
echo ""

# Wait and handle Ctrl+C cleanly
trap "kill $GROQ_PID $VITE_PID 2>/dev/null; echo ''; echo 'Servers stopped.'; exit 0" INT
wait
