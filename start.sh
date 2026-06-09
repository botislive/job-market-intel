#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "Starting backend on :8000..."
cd "$ROOT/backend"
if [ ! -d .venv ]; then
  python3.11 -m venv .venv
  .venv/bin/pip install -r requirements.txt -q
fi
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACK_PID=$!

echo "Starting frontend on :5173..."
cd "$ROOT/frontend"
npm run dev -- --host 0.0.0.0 &
FRONT_PID=$!

trap 'kill $BACK_PID $FRONT_PID 2>/dev/null' EXIT
echo ""
echo "  Dashboard: http://localhost:5173"
echo "  API docs:  http://localhost:8000/docs"
echo ""
wait
