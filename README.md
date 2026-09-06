# 💪 Fitness AI Partner

> **AI-powered fitness tracking backend** — log meals & workouts in *natural language*, let LangGraph agents parse them, ground nutrition estimates with **RAG + pgvector**, and get daily/weekly AI coach insights via Celery.

![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+pgvector-4169E1?logo=postgresql&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1.x-1C3C3C)
![Groq](https://img.shields.io/badge/Groq-gpt--oss--120b-F55036?logo=groq&logoColor=white)
![Gemini Embeddings](https://img.shields.io/badge/Embeddings-Gemini_768--dim-4285F4?logo=google&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.6+-37814A?logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)

---

## 📖 Table of Contents

- [✨ Features](#-features)
- [🧠 Why This Is Awesome](#-why-this-is-awesome)
- [🧗 Problems Solved Along the Way](#-problems-solved-along-the-way)
- [🏗️ Architecture](#️-architecture)
- [⚙️ Tech Stack](#️-tech-stack)
- [📁 Project Structure](#-project-structure)
- [🚀 Getting Started](#-getting-started)
- [🗄️ Database Design](#️-database-design)
- [🤖 AI Agent System](#-ai-agent-system)
- [🔍 RAG Food Retrieval](#-rag-food-retrieval)
- [⏰ Background Jobs (Celery)](#-background-jobs-celery)
- [🔐 Authentication](#-authentication)
- [📡 API Reference](#-api-reference)
- [🖥️ Frontend](#️-frontend)
- [🛡️ Security](#️-security)
- [🧪 Testing](#-testing)
- [📜 License](#-license)

---

## ✨ Features

- **🗣️ Natural Language Logging** — Just tell the AI what you ate/did: *"2 roti aur daal khai"* or *"30 min running."* No tedious form filling.
  - `/agent/parse` classifies intent (meal vs workout) via **RouterAgent (LangGraph)**.
  - `/agent/meals/adjust` & `/agent/workouts/adjust` refine the draft.
  - `/agent/meals/confirm` & `/agent/workouts/confirm` save to DB.
- **🔍 RAG-Grounded Nutrition Estimates** — Instead of pure LLM guessing, verified food data is retrieved from a **pgvector** store (Gemini embeddings), and used to *ground* the LLM's estimate (accurate + explainable). Text generation runs on **Groq**.
- **🤖 AI Coach** — Daily (`/coach/daily`) and weekly coach insights with highlights & suggestions, personalized with the user's profile (BMR/TDEE/BMI) + last 7 days of activity.
- **💬 AI Coach Chat** — Ask the coach anything (`/coach/ask`): diet, workouts, progress. Replies are grounded in the user's profile + recent daily logs, not generic GPT text.
- **🧩 LLM Provider Abstraction** — A single `get_llm()` factory (`app/core/llm.py`); provider is decided by `.env` (Groq default, Gemini reference). Swap providers without touching agents.
- **🎯 Smart Targets** — BMR/TDEE calculation with goal-based macro suggestions (`/coach/suggest-target`).
- **📊 Daily Log Aggregation** — Denormalized per-day totals with incremental sync and a `recalculate` repair endpoint.
- **🕐 Timezone-Correct Days** — All date bucketing uses **Asia/Karachi** (PKT): meals/workouts logged after local midnight land on *today*, never "yesterday" (UTC bug).
- **⏰ Celery Beat Scheduler** — Daily coach at 11 PM, weekly report every Monday 6 AM, without blocking the API.
- **🍽️ USDA Integration** — Reference nutrition data cross-checked against USDA FoodData Central.
- **🔐 Secure JWT Auth** — Access (30 min) + refresh (7 days) tokens with type-guard, bcrypt-hashed passwords.

---

## 🧠 Why This Is Awesome

This isn't a CRUD app with an AI bolted on. It's a genuine **backend + AI engineering** showcase:

- **Agentic workflows** built with LangGraph `StateGraph` (stateful, conditional routing) — not single prompts.
- **RAG pipeline** — embeddings → pgvector `cosine_distance` → grounded context — the right way to do reliable AI predictions.
- **Production background processing** — Celery beat, fan-out tasks, async-in-sync bridges, rate-limit retries, NullPool, idempotent upserts.
- **Confidence-aware UX** — the AI never silently stores guessed data; it asks for clarification (`is_confident=false`) and you confirm before saving.

---

## 🧗 Problems Solved Along the Way

Real bugs I hit while building this — and the engineering behind the fixes:

1. **Free-tier rate limits were breaking the UX.** Google Gemini's free tier 429s killed meal parsing — literally 50-second stalls. Fix: a `get_llm()` provider factory (`app/core/llm.py`) and moved all text generation to **Groq** `openai/gpt-oss-120b` (30 req/min free). Swapping providers is now a one-line `.env` change; agents don't know *which* LLM they're talking to. Embeddings stay on Gemini (Groq offers no embeddings API) — different quotas, barely a concern.

2. **The LLM's structured output was unreliable.** It sometimes returned `{"classification": ...}` instead of the schema's `{"intent": ...}`, or refused to call tools at all. Fix: `with_structured_output(Model, method="json_mode")` **plus** injecting the exact Pydantic JSON schema (`json_schema_instruction()` via `model_json_schema()`) into every structured prompt. Parsing went from flaky to deterministic.

3. **"Never empty" policy for AI requests.** If the LLM is down, the target engine silently fails — bad for a fitness app. Fix: TargetAgent falls back to honest **BMR/TDEE/BMI formulas** (`source: "ai"` vs `source: "math"`), and every user-facing AI endpoint fails fast with a graceful, structured error instead of a raw 500.

4. **The "meals landed on yesterday" timezone bug.** Timestamps are stored as UTC, so a meal logged after midnight (PKT) bucketed into the *previous* day's daily log — totals silently wrong. Fix: standardized everything to **Asia/Karachi** in `app/core/dates.py` (`local_date()` for bucketing, `day_range()` for indexable TZ-safe range filters, `today_local()`), and frontend `todayISO()` matches via `Intl.DateTimeFormat` with the same timezone. "Today" now always means the user's calendar today.

---

## 🏗️ Architecture

```text
                        ┌─────────────────────────────────────────────────┐
                        │              React + Vite Frontend              │
                        │       (meals, workouts, dashboard, coach)       │
                        └───────────────────────┬─────────────────────────┘
                                                │ HTTPS / JSON (JWT Bearer)
                                                ▼
                        ┌─────────────────────────────────────────────────┐
                        │                   FastAPI (async)               │
                        │         10 routers · Pydantic validation         │
                        │         get_current_user dependency              │
                        └───────┬──────────────────────────┬──────────────┘
                                │                          │
                    ┌───────────▼──────────┐      ┌────────▼───────────────┐
                    │   AI Agent Layer     │      │   Service Layer         │
                    │  LangGraph StateGraph │      │  auth · meal · workout  │
                    │  Router/Nutrition/    │      │  daily_log · weekly     │
                    │  Workout/Coach/Target │      │  embedding · retrieval  │
                    └───────────┬──────────┘      │  usda                   │
                                │                 └────────┬──────────────┘
                                │                          │
                    ┌───────────▼───────────────────────────▼──────────┐
                    │              Groq LLM (text generation)          │
                    │      gpt-oss-120b · structured · chat            │
                    │      via get_llm() factory (app/core/llm.py)     │
                    │      + Gemini text-embedding (768-dim) for RAG    │
                    └───────────────────────┬───────────────────────────┘
                                            │
┌───────────────────────┐        ┌──────────▼────────────────────────────┐
│  Celery Beat Scheduler │        │           PostgreSQL 16               │
│  daily coach 23:00     │ sends  │    users · meals · workouts            │
│  weekly report Mon 6am │───────▶│    daily_logs · weekly_reports         │
└───────────┬───────────┘ Redis   │    foods (+ pgvector Vector(768))      │
            │             broker  └───────────────────────────────────────┘
            ▼
   Celery Workers (async-in-sync, fan-out, retry)
```

### Request Lifecycle

1. Client sends request with `Authorization: Bearer <JWT>`.
2. `get_current_user` dependency validates the JWT (rejects refresh token, extracts `sub`).
3. Router → Service (business logic) → DB (async SQLAlchemy) / Agent (LLM).
4. AI agents (LangChain + LangGraph) call **Groq** through the shared `get_llm()` factory (embeddings stay on Google Gemini).
5. Heavy scheduled work (coach/report generation) delegates to Celery.

---

## ⚙️ Tech Stack

| Layer             | Technology                                           | Why                                                                      |
|-------------------|------------------------------------------------------|--------------------------------------------------------------------------|
| **Framework**     | FastAPI 0.141 (async)                                | Async I/O, Pydantic validation, auto OpenAPI docs                        |
| **ORM / DB**      | SQLAlchemy 2.0 async + asyncpg + PostgreSQL 16       | Type-safe async ORM, pgvector support                                    |
| **Vector DB**     | pgvector (`Vector(768)`)                             | In-DB semantic search via `cosine_distance`                              |
| **Agents**        | LangGraph 1.x + LangChain                            | Stateful, multi-step agent orchestration                                 |
| **LLM**           | Groq — `openai/gpt-oss-120b`                      | Free tier (30 req/min), classification, parsing, insights, coach chat |
| **LLM Abstraction**| `get_llm()` factory (`app/core/llm.py`) | Provider decided by `.env` — swap LLMs without touching agents |
| **Embeddings**    | Gemini text-embedding (768-dim)                      | Food text → vector for RAG (Groq has no embeddings API) |
| **Background**    | Celery 5.6 + Redis 7 (broker/backend + beat)         | Scheduled daily/weekly AI generation                                     |
| **Auth**          | python-jose (JWT) + bcrypt (passlib)                 | Stateless access/refresh tokens                                          |
| **External**      | USDA FoodData Central API + httpx (async)            | Trusted nutrition reference                                              |
| **Migrations**    | Alembic                                             | Versioned schema migrations                                              |
| **Frontend**      | React + Vite                                         | Fast SPA consuming the API                                               |

---

## 📁 Project Structure

```text
fitness-ai-partner/
├── app/
│   ├── main.py                 # FastAPI app + router registration
│   ├── core/                   # config · security (JWT/bcrypt) · deps · celery_app · llm.py · dates.py
│   ├── db/                     # base · async session
│   ├── models/                 # user · food · meal · workout · daily_log · weekly_report
│   ├── schemas/                # Pydantic request/response DTOs
│   ├── api/                    # auth · meal · workout · daily_log · entry/meal/workout_agent
│   │                           #   coach_agent · target_agent · weekly_report
│   ├── agents/                 # LangGraph agents: router · nutrition · workout · coach · target
│   ├── services/               # embedding · food_retrieval · usda · daily_log · meal
│   │                           #   workout · weekly_report · auth
│   └── tasks/                  # Celery tasks: coach_tasks · weekly_report_tasks
├── alembic/                    # migrations
├── scripts/seed_foods.py       # USDA-verified food + embedding seeding
├── frontend/                   # React + Vite SPA
├── docker-compose.yml          # pgvector DB + Redis
├── requirements.txt
└── .env.example                # configuration template
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for the frontend)
- Docker (for PostgreSQL + Redis)

### 1. Clone & configure

```bash
git clone https://github.com/MuhammadHaider1/fitness-ai-partner.git
cd fitness-ai-partner
cp .env.example .env
# edit .env — add your GROQ_API_KEY, USDA_API_KEY and SECRET_KEY
```

### 2. Start the infrastructure

```bash
docker compose up -d
```

This starts:
- **PostgreSQL + pgvector** on port `5436` (db: `fitness_ai_db`, user: `fitness_admin`)
- **Redis** on port `6381`

### 3. Python environment & install

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run migrations & seed foods (optional)

```bash
alembic upgrade head
python scripts/seed_foods.py    # populates the verified food table + embeddings
```

### 5. Run the backend

```bash
uvicorn app.main:app --reload
```

- Interactive docs: <http://localhost:8000/docs>

### 6. Run Celery (background jobs)

```bash
# In separate terminals:
celery -A app.core.celery_app.celery_app worker --loglevel=info
celery -A app.core.celery_app.celery_app beat --loglevel=info
```

### 7. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

---

## 🗄️ Database Design

### Entity Relationships

```text
users ──────< meals          (1:N)  user's logged meals
users ──────< workouts       (1:N)  user's logged workouts
users ──────< daily_logs     (1:N)  per-day aggregate (unique user+date)
users ──────< weekly_reports (1:N)  per-week AI report (unique user+week)

foods (reference/verified nutrition + pgvector embedding)
```

### Models

| Model          | Key Fields                                                        | Purpose                                          |
|----------------|-------------------------------------------------------------------|--------------------------------------------------|
| **User**       | `email (unique)`, `hashed_password`, `full_name`, `age`, `height_cm`, `weight_kg`, `gender`, `goal`, `activity_level` | Auth + fitness profile for BMR/TDEE              |
| **Food**       | `name`, `description`, `calories`, `protein_g/carbs_g/fats_g`, `embedding (Vector 768)` | Verified reference data + vector for RAG         |
| **Meal**       | `user_id`, `raw_text`, `food_name`, `meal_type`, `calories`, macros, `source (manual/agent)` | Raw + parsed meal entry                          |
| **Workout**    | `user_id`, `raw_text`, `workout_type (cardio/strength)`, `name`, `duration/distance` or `sets/reps/weight`, `intensity`, `calories_burned`, `source` | Cardio & strength entries                        |
| **DailyLog**   | `user_id`, `log_date`, `calorie_target`, `total_calories/protein/carbs/fats`, `water_intake_ml`, `mood`, `notes`, `calories_burned` | `UNIQUE(user_id, log_date)`; per-day aggregates  |
| **WeeklyReport**| `user_id`, `week_start`, `week_end`, `summary`, `highlights (JSON)`, `suggestions (JSON)` | `UNIQUE(user_id, week_start)`; AI generated      |

### Design Rationale

- **Denormalized `DailyLog`** — frequent "today/overview" reads are fast without summing meals every time. `apply` keeps totals in sync incrementally, while `recalculate` repairs them from the source of truth (the `meals`/`workouts` tables).
- **`Vector(768)` on `Food`** — Gemini's text-embedding output dimension; small enough for fast cosine search but semantically rich.
- **`source (manual/agent)`** — data provenance: distinguishes user-entered from AI-parsed entries for trust & debugging.
- **Unique constraints** — one daily log per user/date, one weekly report per user/week → race-safe against duplicate generation.
- **`log_date` = Asia/Karachi calendar day** — bucketed via `app/core/dates.py` (`local_date`/`day_range`), so per-day totals always line up with the user's local "today".

---

## 🤖 AI Agent System

Built with **LangGraph `StateGraph`** — stateful, conditional, modular.

| Agent            | Role                                                            | Structured Output            |
|------------------|-----------------------------------------------------------------|------------------------------|
| **RouterAgent**  | Classify intent (meal/workout) + conditional route              | `IntentClassification`       |
| **NutritionAgent**| RAG retrieval + meal parsing (nutrition estimate)               | `ParsedMeal` (confidence)    |
| **WorkoutAgent** | Parse workout (type, sets, calories)                            | `ParsedWorkout`              |
| **CoachAgent**   | Daily & weekly insight + **open-ended chat** (`chat_with_coach`, profile + 7-day context) | `Daily/WeeklyCoachInsight` / plain text |
| **TargetAgent**  | BMR/TDEE + goal-based macro suggestion                          | `SuggestedTarget`            |

> **Structured output reliability:** every structured agent uses `with_structured_output(Model, method="json_mode")` **plus** `json_schema_instruction(Model)` — the exact Pydantic JSON schema (`model_json_schema()`) is injected into the prompt. This eliminated the LLM returning wrong keys or skipping tool calls. All agents get their model through the shared `get_llm()` factory.

### RouterAgent (LangGraph flow)

```text
                ┌────────────────── StateGraph(RouterState) ──────────────────┐
                │                                                             │
                │   classify_intent ──route_by_intent──▶ parse_meal ─▶ validate ─▶ END
                │                                            └─▶ parse_workout ─▶ END
                └─────────────────────────────────────────────────────────────┘
```

- `StateGraph(TypedDict)` state passes between nodes.
- LLM classifier (`temperature=0`) decides intent.
- `add_conditional_edges` + `route_by_intent` route to the correct parser.
- The router **reuses** the nutrition/workout parsers (DRY).
- A **`validate` node** defensively downgrades `is_confident` if a critical field is unexpectedly missing — the user never gets broken data.

### Confidence & Clarification Flow

A vague input like *"kuch khaya"* → `is_confident=false` + a specific clarification question. The user replies → `adjust` refines the draft → `confirm` saves. The app never silently persists guessed/made-up data.

---

## 🔍 RAG Food Retrieval

Retrieval-Augmented Generation grounds the LLM's nutrition estimate in **verified facts** instead of guessing.

```text
seed_foods.py ──▶ USDA-verified foods + South Asian dishes
                        │
                        ▼
   Gemini embedding (768-dim) ──▶ pgvector Vector(768) on foods.embedding
                        │
                        ▼
   user query "roti aur daal" ──▶ embed ──▶ cosine_distance top 3 foods
                        │
                        ▼
   retrieved verified context ──▶ NutritionAgent prompt ──▶ grounded estimate + reasoning
```

> **Provider split:** embeddings are Gemini (768-dim), generation is **Groq** — two different quotas, both on free tiers.

- **Cosine distance** measures semantic direction — ideal for matching similar food text.
- **USDA FoodData Central** supplies trusted per-100g values for seeded ingredients.
- The `reasoning` field makes each estimate **explainable**.

---

## ⏰ Background Jobs (Celery)

| Beat Schedule        | Task                                      | When                         |
|----------------------|-------------------------------------------|------------------------------|
| `daily-coach-every-night`   | `generate_daily_coach_for_all_users`      | Every day at **23:00** (Asia/Karachi) |
| `weekly-report-every-monday`| `generate_weekly_reports_for_all_users`   | Every **Monday 06:00**       |

### Design highlights

- **Fan-out**: a batched task fetches all user IDs, then `.delay()`s an individual task per user → one user's failure doesn't block others, and work distributes across workers.
- **Async-in-sync bridge**: synchronous Celery tasks run async DB/AI via `asyncio.run(...)`.
- **NullPool worker engine**: per-task DB connections prevent pool exhaustion.
- **Rate-limit retry**: on LLM `429 / RESOURCE_EXHAUSTED` (Groq/Gemini), `self.retry(countdown=25)` recovers gracefully.
- **Idempotent upsert**: weekly report uses `UNIQUE(user_id, week_start)` — existing updated, missing created.

---

## 🔐 Authentication

- **bcrypt** password hashing (passlib).
- **JWT access token** (30 min) + **refresh token** (7 days).
- Refresh tokens carry a `"type": "refresh"` claim; `get_current_user` **rejects** them to prevent API misuse.
- All user-data queries are scoped to `current_user.id` (data isolation).

| Endpoint             | Method | Description                             |
|----------------------|--------|-----------------------------------------|
| `/auth/register`     | POST   | Register a user (returns profile)       |
| `/auth/login`        | POST   | Login → access + refresh tokens         |
| `/auth/refresh`      | POST   | Exchange a valid refresh for a new pair |
| `/auth/me`           | GET    | Current user profile                    |

---

## 📡 API Reference

### Auth — `/auth`
| Endpoint       | Method | Description            |
|----------------|--------|------------------------|
| `/register`    | POST   | Register user          |
| `/login`       | POST   | Login → tokens         |
| `/refresh`     | POST   | Refresh tokens         |
| `/me`          | GET    | Current profile        |

### Meals — `/meals`
| Endpoint | Method | Description              |
|----------|--------|--------------------------|
| `/`      | POST   | Create meal (structured) |
| `/`      | GET    | List user meals          |
| `/{id}`  | GET    | Get one meal             |
| `/{id}`  | PATCH  | Update meal              |
| `/{id}`  | DELETE | Delete meal              |

### Workouts — `/workouts`
| Endpoint | Method | Description                 |
|----------|--------|-----------------------------|
| `/`      | POST   | Create workout (structured) |
| `/`      | GET    | List user workouts          |
| `/{id}`  | PATCH  | Update workout              |
| `/{id}`  | DELETE | Delete workout              |

### Daily Log — `/daily-log`
| Endpoint       | Method | Description                        |
|----------------|--------|------------------------------------|
| `/`            | GET    | Today's (or queried date) log      |
| `/history`     | GET    | Log history                        |
| `/summary`     | GET    | Streak/averages summary            |
| `/`            | PATCH  | Update target/water/mood/notes     |
| `/recalculate` | POST   | Rebuild totals from meals/workouts |

### AI Agents
| Endpoint                   | Method | Description                              |
|----------------------------|--------|------------------------------------------|
| `/agent/parse`             | POST   | Classify intent → draft (meal/workout)   |
| `/agent/meals/adjust`      | POST   | Refine meal draft from feedback          |
| `/agent/meals/confirm`     | POST   | Save meal draft                          |
| `/agent/workouts/adjust`   | POST   | Refine workout draft                     |
| `/agent/workouts/confirm`  | POST   | Save workout draft                       |

### Coach & Targets — `/coach`
| Endpoint           | Method | Description                          |
|--------------------|--------|--------------------------------------|
| `/daily`           | GET    | Daily AI coach insight               |
| `/ask`             | POST   | Coach chat — profile + last-7-days context |
| `/suggest-target`  | GET    | Goal-based calorie/macro targets     |

### Weekly Report — `/weekly-report`
| Endpoint     | Method | Description                       |
|--------------|--------|-----------------------------------|
| `/generate`  | POST   | Request/generate weekly report    |
| `/`          | GET    | List weekly reports               |

> Full interactive docs available at `/docs` (Swagger) and `/redoc` when the server is running.

---

## 🖥️ Frontend

A modern **React + Vite** single-page app (in `frontend/`) that consumes this API, featuring:

- **Auth screens** — signup / login.
- **Dashboard** — today's calories/protein vs target, water, mood, calorie ring.
- **AI Logging** — a chat-style input to log meals & workouts in natural language via `/agent/parse` → adjust → confirm.
- **History** — meal/workout lists and daily log summary.
- **Coach panel** — daily/weekly insights & suggested targets + a **💬 Ask** tab for the conversational AI coach.

> The frontend was built **with AI assistance** — it exists to showcase the backend's capabilities. The real engineering depth here is backend and AI architecture.

```bash
cd frontend
npm install
npm run dev        # dev server on http://localhost:5173
npm run build      # production build
```

Backend must be running on `http://localhost:8000` (CORS is configured for the Vite origin).

---

## 🛡️ Security

- Passwords hashed with **bcrypt** — never stored in plaintext.
- **JWT** signed with a secret, short-lived access + refresh rotation.
- `get_current_user` guards protected endpoints and scopes queries to the authenticated user.
- Secrets managed via `.env` (never committed — see `.gitignore`).
- (Recommended for production) HTTPS, rate limiting, secrets manager, and RBAC hardening.

---

## 🧪 Testing

```bash
# Run the backend with the Python test runner you prefer (pytest if configured)
pytest
```

> No test suite is committed yet — a great first contribution. Add tests for the auth flow, the entry agent parse→confirm flow, and the daily-log aggregation/recalculate consistency.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
  <sub>Built with ❤️ — FastAPI · LangGraph · Groq · Gemini Embeddings · pgvector · Celery</sub>
</div>
