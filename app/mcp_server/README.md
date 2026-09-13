# Fitness AI Partner — MCP Server

`app/mcp_server/server.py` hamare existing FastAPI/Groq backend ko ek
[MCP](https://modelcontextprotocol.io) (Model Context Protocol) server ke
roop mein expose karta hai — taake koi bhi MCP-compatible AI client (Claude
Desktop, Claude Code, Cursor, etc.) directly hamari fitness data pe kaam kar
sake.

> **"Agentic layer is messenger, not brain"** — saara domain logic wahi
> services/agents hai jo REST API use karta hai; MCP sirf unke liye aasan,
> natural-language wrappers deta hai. Logic ek jagah, do entry points.

---

## Architecture Overview

```
Claude Desktop / Claude Code            FastAPI app                      PostgreSQL + PGVector
        │                                │
        │  MCP (stdio JSON-RPC)          │
        │ ──────────────────────────────►│
        │                                │ app.mcp_server.server.py
        │                                │   ├─ FastMCP("fitness-ai-partner")
        │                                │   ├─ 7 tools (2 write, permission-gated)
        │                                │   │
        │                                │   └─ reuses:
        │                                │      AsyncSessionLocal (app/db/session.py)
        │                                │      meal_service · workout_service
        │                                │      daily_log_service · auth_service
        │                                │      nutrition_agent · workout_agent · coach_agent
```

**Key decisions (yehi design ka "because" hai):**

| Decision | Why |
|---|---|
| MCP server same process re-use karta hai services/agents | Duplicate business logic nahi banani padti; test ka proof. |
| Har tool call me `async with AsyncSessionLocal() as db:` | Same DB session source as FastAPI endpoints; auto-close. |
| Write tools (`*_from_text`) par `confirm/`pehle preview` pattern | Agent kabhi silently data mutate na kare: pehla call sirf parsed DRAFT deta hai, DB me KUCH nahi likhta. Exact values + `confirm=True` par hi save. |
| `confirm=True` par parsed values manually pass karne ka option | Re-parsing non-deterministic hota hai (LLM); preview wali exact values pass karke deterministic save. |
| `_require_user()` har tool me | `get_or_create_daily_log` FK bina validate kare crash se pehle catch — clean MCP error. |
| `mcp==1.30.0` (v1 API) pinned | mcp 2.x me `FastMCP` rename ho gaya `MCPServer`; v1 hi stable, widespread API hai. |

---

## Tools

### Read-only (data query)
1. **`get_daily_summary(user_id, log_date)`** — ek din ka `DailyLog`: calorie target,
   total calories, protein/carbs/fats (g), calories burned, water intake, mood.
2. **`get_meal_history(user_id, log_date)`** — us din ki saari meals (food, macros,
   source, timestamp).
3. **`get_workout_history(user_id, log_date)`** — us din ke saare workouts.
4. **`get_weekly_streak_summary(user_id, start_date, end_date)`** — range me aggregate:
   days logged/on-target, averages, current streak (consistency tracking).
5. **`get_daily_coach_insight(user_id, log_date)`** — AI coach se daily
   summary/highlights/suggestions (LLM call; 429-friendly error).

### Write (permission-gated)
6. **`log_meal_from_text(user_id, raw_text, confirm=False, [values...])`**
7. **`log_workout_from_text(user_id, raw_text, confirm=False, [values...])`**

**Meal/Workout write ka flow:**

```
Call 1 (confirm=False)  → nutrition_agent/workout_agent parse karta hai
                          → draft return (is_confident, values, reasoning)
                          → X  kuch save nahi hota X
Call 2 (confirm=True + exact values) → meal_service/workout_service save
                          → DailyLog totals sync  → saved record return
```

Agar `confirm=True` par values nahi di gayi to dobara parse hota hai, lekin
sirf tab jab draft `is_confident` ho — warna clean error.

---

## Setup

### 1. Install

```bash
cd /home/haider/fitness-ai-partner
venv/bin/python -m pip install "mcp<2"   # == 1.30.0
```

### 2. Manual run (test)

```bash
venv/bin/python -m app.mcp_server.server
```

Ye stdio transport par chalega — bas `Ctrl+C` se band karo.

### 3. Claude Desktop integration

`claude_desktop_config.json` (Windows: `%APPDATA%\Claude\` · macOS:
`~/Library/Application Support/Claude/`) me add karo:

```json
{
  "mcpServers": {
    "fitness-ai-partner": {
      "command": "/home/haider/fitness-ai-partner/venv/bin/python",
      "args": ["-m", "app.mcp_server.server"],
      "cwd": "/home/haider/fitness-ai-partner"
    }
  }
}
```

> `cwd` project root hona zaroori hai — `app.*` imports wahin se resolve hote
> hona (pyproject/dotenv, `app/db/session.py`).

### 4. Claude Code integration

```bash
claude mcp add fitness-ai-partner \
  -- /home/haider/fitness-ai-partner/venv/bin/python -m app.mcp_server.server
# ya project scope ke liye --scope project
```

---

## Verification checklist (khud check karne ke liye)

```bash
# 1. Server import + tool registration
cd /home/haider/fitness-ai-partner && venv/bin/python -c "
from app.mcp_server.server import mcp
print(mcp._tool_manager.list_tools())"

# 2. Live DB smoke test (pehla user use hota hai)
venv/bin/python - <<'EOF'
import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.mcp_server import server

async def main():
    async with AsyncSessionLocal() as db:
        uid = (await db.execute(select(User.id).limit(1))).scalar_one()
    print(await server.get_daily_summary(str(uid), "2026-09-13"))
asyncio.run(main())
EOF
```

---

## GUI testing (browser — MCP Inspector)

CLI ke baghair mouse se tools test karne ke liye official MCP Inspector use karo.

```bash
cd /home/haider/fitness-ai-partner
bash run_inspector.sh
```

Script 2 cheezein uthaata hai:
1. **MCP server @ SSE** — `mcp_sse_entry.py` hamaara server `127.0.0.1:9000/sse`
   par expose karta hai (port 8000 bilkul nahi — wo FastAPI API ka hai).
2. **Inspector UI @ `http://127.0.0.1:6274`** — browser GUI (Node >=20 zaroori,
   is liye script `~/.nvm/versions/node/v20.20.2/bin` use karta hai; node18 par
   inspector v2 `styleText` error deta hai).

UI click-path:
1. `Transport Type` = **SSE**
2. `URL` = `http://127.0.0.1:9000/sse`
3. **Connect** → left panel mein 7 tools list hongi.
4. Tool select karo → `Arguments` JSON bharo → **Run Tool**.

Example arguments (aapka test user id ho to usse replace karo):
```json
{ "user_id": "0d1b2e5b-7b1e-4c56-b854-f4211fba5132", "log_date": "2026-09-13" }
```

`log_meal_from_text` par preview dekho (`confirm` omit/`false` → sirf draft,
kuch save nahi hota), phir `confirm: true` + wohi exact values bhej kar save.

>

---
## Failure modes (sab friendly errors)

| Condition | Behaviour |
|---|---|
| Invalid `user_id` | `ValueError` ciclo: "user_id ek valid UUID hona chahiye..." |
| Invalid ISO date | `ValueError`: "log_date ek valid ISO date hona chahiye..." |
| User not in DB | `ValueError`: "User with id '...' nahi mila" |
| `/` LLM rate limit (429) | coach insight: `{"error": "AI coach abhi busy hai..."}` |
| LLM parse failure | `ValueError`: "Meal parse nahi hua: ..." |
| `confirm=True` bina exact values / not confident | Clean error: "pehle preview le kar exact values bhejo..." |

---

## Job-interview talking points

- MCP server is **staleless transport, stateless tools** — identity (OAuth) aur
  authorization ka question codebase me `get_current_user` (FastAPI middleware)
  par hai; MCP direct-DB tools hone ki wajah se `_require_user` guard kyoon
  add kiya ("security at the boundary").
- **Prevention-over-privilege** design: write tools sirf allowed-unconfirmed
  preview dete hain — "least privilege" pattern AI-agents ke liye.
- **Why FastMCP (v1) not mcp 2.x**: eco-system compatibility, `@mcp.tool()`
  decorator ergonomics, documented widely; 2.x rename (`FastMCP`→`MCPServer`)
  is breaking-change signal we deliberately pinned.

---

## Structure

```
app/mcp_server/
├── __init__.py   # package docstring (why MCP)
└── server.py     # FastMCP instance, 7 tools, helpers, mcp.run()
```