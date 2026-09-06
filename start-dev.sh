#!/usr/bin/env bash
# Fitness AI Partner — dev launcher
# Chalao: ./start-dev.sh
# Ye 3 alag terminals kholta hai: Backend, Celery worker/beat, aur Frontend.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v gnome-terminal >/dev/null 2>&1 && TERM_CMD="gnome-terminal"
command -v x-terminal-emulator >/dev/null 2>&1 && TERM_CMD="x-terminal-emulator"
command -v konsole >/dev/null 2>&1 && TERM_CMD="konsole"

if [[ -z "$TERM_CMD" ]]; then
  echo "❌ Koi terminal emulator nahi mila (gnome-terminal/x-terminal-emulator)."
  echo "Aap khud 3 terminals khol ke neeche wale commands chala sakte hain:"
  cat <<'EOF'

  ========== TERMINAL 1 (backend) ==========
  cd "/home/haider/fitness-ai-partner"
  source venv/bin/activate
  uvicorn app.main:app --reload

  ========== TERMINAL 2 (celery worker + beat) ==========
  cd "/home/haider/fitness-ai-partner"
  source venv/bin/activate
  celery -A app.core.celery_app.celery_app worker --loglevel=info &
  celery -A app.core.celery_app.celery_app beat --loglevel=info

  ========== TERMINAL 3 (frontend) ==========
  cd "/home/haider/fitness-ai-partner/frontend"
  npm run dev
EOF
  exit 1
fi

# Docker (DB + Redis) check
if ! docker info >/dev/null 2>&1; then
  echo "⚠️  Docker nahi chal raha. Pehle DB aur Redis ke liye docker start karo."
  read -r -p "Docker compose up karoon? (y/n): " ans
  if [[ "$ans" == "y" ]]; then
    docker compose -f "$ROOT/docker-compose.yml" up -d
  fi
else
  # Check containers up hain ya nahi
  if ! docker ps --format '{{.Names}}' | grep -qE 'fitness_ai_db|fitness_ai_redis'; then
    echo "⚙️  DB/Redis containers start karta hoon..."
    docker compose -f "$ROOT/docker-compose.yml" up -d
  else
    echo "✅ DB/Redis already running."
  fi
fi

echo "🚀 3 terminals kholta hoon — pehle npm install kya? (venv pehli dafa setup kar chuke hain to skip)"
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  echo "Frontend deps install kar raha hoon (pehli dafa)..." 
  (cd "$ROOT/frontend" && npm install)
fi

if [[ "$TERM_CMD" == "gnome-terminal" ]]; then
  gnome-terminal --title="Fitness-AI Backend (FastAPI)" -- bash -lc "
    cd '$ROOT'; source venv/bin/activate; uvicorn app.main:app --reload; exec bash"
  gnome-terminal --title="Fitness-AI Celery" -- bash -lc "
    cd '$ROOT'; source venv/bin/activate;
    celery -A app.core.celery_app.celery_app worker --loglevel=info --detach;
    celery -A app.core.celery_app.celery_app beat --loglevel=info; exec bash"
  gnome-terminal --title="Fitness-AI Frontend (Vite)" -- bash -lc "
    cd '$ROOT/frontend'; npm run dev; exec bash"
elif [[ "$TERM_CMD" == "x-terminal-emulator" ]]; then
  x-terminal-emulator -e bash -lc "cd '$ROOT'; source venv/bin/activate; uvicorn app.main:app --reload; exec bash" &
  x-terminal-emulator -e bash -lc "cd '$ROOT'; source venv/bin/activate; celery -A app.core.celery_app.celery_app beat --loglevel=info; exec bash" &
  x-terminal-emulator -e bash -lc "cd '$ROOT/frontend'; npm run dev; exec bash" &
fi

echo "✅ Done. Backend :8000, Frontend :5173"
