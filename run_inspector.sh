#!/usr/bin/env bash
# =============================================================================
# MCP Inspector GUI — "frontend se test" (browser UI, mouse se tools chalane ke liye)
#
#   bash run_inspector.sh
#
# Kya karta hai:
#   1. Purane :9000 / :6274 listeners saaf karta hai
#   2. MCP server ko SSE transport par chalaata hai (127.0.0.1:9000)
#   3. MCP Inspector browser UI kholta hai (node20 use karte hue — node18 par
#      inspector v2 nahi chalta: "styleText" error)
#
# Baad mein Ctrl+C nai hota background mein — band karne ke liye:
#   pkill -f mcp_sse_entry.py ; pkill -f modelcontextprotocol
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")"

NODE20="$HOME/.nvm/versions/node/v20.20.2/bin"

# 1) stale listeners clean
for p in 9000 6274 6275 6277; do
  pid=$(ss -tlnp 2>/dev/null | grep ":$p " | grep -oP 'pid=\K[0-9]+' | head -1)
  [ -n "${pid:-}" ] && kill "$pid" 2>/dev/null
done
sleep 1

# 2) MCP server — SSE transport (hamara app, port 9000)
nohup venv/bin/python mcp_sse_entry.py > /tmp/mcp_sse_server.log 2>&1 &
sleep 3

# 3) Inspector UI
PATH="$NODE20:$PATH" nohup npx -y @modelcontextprotocol/inspector > /tmp/mcp_inspector.log 2>&1 &
sleep 12

URL=$(grep -oP 'http://127.0.0.1:6274[^ ]*' /tmp/mcp_inspector.log | tail -1)
URL="${URL:-http://127.0.0.1:6274}"
TOKEN_URL=$(grep -oP 'http://localhost:6274[^ ]*' /tmp/mcp_inspector.log | tail -1)

echo "============================================================================"
echo "[1] MCP server (SSE)  : http://127.0.0.1:9000/sse  (log: /tmp/mcp_sse_server.log)"
echo "[2] Inspector UI kholo: ${URL}"
[ -n "${TOKEN_URL:-}" ] && echo "    (token wala URL: ${TOKEN_URL})"
echo "============================================================================"
echo ""
echo "UI mein (browser mein URL khol ker):"
echo " 1. Left panel 'Transport Type' = SSE"
echo " 2. URL box = http://127.0.0.1:9000/sse"
echo " 3. 'Connect' press karo -> left Tools list mein 7 tools aayengi"
echo ""
echo "Tool chalane ka example:"
echo "   Tool: get_daily_summary"
echo "   Arguments JSON: {\"user_id\": \"0d1b2e5b-7b1e-4c56-b854-f4211fba5132\", \"log_date\": \"2026-09-13\"}"