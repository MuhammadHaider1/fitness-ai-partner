# Fitness AI Partner — Frontend

React + Vite single-page application for the **Fitness AI Partner** backend.

## Features

- 🔐 **Auth** — signup with full fitness profile, login, token refresh.
- 📊 **Dashboard** — today's calories/protein/water ring, macros vs target, recent meals & workouts.
- 🗣️ **AI Logging** — the star feature: type natural language, AI parses it (`/agent/parse`), you adjust or confirm. Handles confidence + clarification flow.
- 🎯 **AI Coach** — daily insight chat, BMR/TDEE suggested targets, weekly reports (auto + on-demand).
- 📈 **History** — daily-log summary, streak, averages, and deletable meal/workout tables.
- ⚙️ **Settings** — update profile + today's calorie target, water, mood, notes.

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_BASE if backend is not on :8000
npm run dev            # http://localhost:5173
```

The Vite dev server proxies requests to the FastAPI backend on `http://localhost:8000`. Ensure the backend + DB are running (see the root `README.md`).

## Production build

```bash
npm run build
npm run preview
```

## Structure

```text
src/
├── App.jsx            # routing + providers
├── main.jsx           # entry
├── index.css          # design system (CSS variables, components)
├── context/AuthContext.jsx
├── services/api.js    # axios instance + auth interceptor
├── services/format.js
├── components/        # Layout, ui (Stat, Ring, Pill, Empty, …)
└── pages/             # Login, Register, Dashboard, AILogging, History, Coach, Settings, NotFound
```