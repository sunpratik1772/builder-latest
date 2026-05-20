#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUN_DIR="$ROOT_DIR/.run"
LOG_DIR="$RUN_DIR/logs"

BACKEND_PORT=8001
FRONTEND_PORT=3000
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"

if ! command -v lsof >/dev/null 2>&1; then
  echo "Error: lsof is required but not installed."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required but not installed."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "Error: npm is required but not installed."
  exit 1
fi

mkdir -p "$LOG_DIR"

echo "Stopping existing dbSherpa backend/frontend processes only..."

# Stop previously tracked PIDs first.
if [ -f "$RUN_DIR/backend.pid" ]; then
  pid="$(cat "$RUN_DIR/backend.pid" 2>/dev/null || true)"
  if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
  fi
  rm -f "$RUN_DIR/backend.pid"
fi

if [ -f "$RUN_DIR/frontend.pid" ]; then
  pid="$(cat "$RUN_DIR/frontend.pid" 2>/dev/null || true)"
  if [ -n "${pid:-}" ] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
  fi
  rm -f "$RUN_DIR/frontend.pid"
fi

# Free only our two service ports; do not touch unrelated ports/apps.
for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
  pids="$(lsof -ti :"$port" 2>/dev/null || true)"
  if [ -n "${pids}" ]; then
    echo "$pids" | xargs kill 2>/dev/null || true
  fi
done

# Match only processes started from this repo to avoid killing unrelated apps.
pkill -f "$ROOT_DIR/backend.*uvicorn server:app" 2>/dev/null || true
pkill -f "$ROOT_DIR/frontend.*vite" 2>/dev/null || true
pkill -f "$ROOT_DIR/frontend.*npm start" 2>/dev/null || true

sleep 1

wait_for_port() {
  local port="$1"
  local name="$2"
  local attempts=20
  local i

  for ((i=1; i<=attempts; i++)); do
    if lsof -ti :"${port}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done

  echo "${name} failed to start on port ${port} after ${attempts}s."
  return 1
}

BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

echo "Starting backend on port ${BACKEND_PORT}..."
(
  cd "$BACKEND_DIR"
  nohup python3 -m uvicorn server:app --host 0.0.0.0 --port "${BACKEND_PORT}" >"$BACKEND_LOG" 2>&1 &
  echo $! > "$RUN_DIR/backend.pid"
)

sleep 2
if ! wait_for_port "${BACKEND_PORT}" "Backend"; then
  echo "Backend failed to start. Check: $BACKEND_LOG"
  exit 1
fi

echo "Starting frontend on port ${FRONTEND_PORT}..."
(
  cd "$FRONTEND_DIR"
  nohup npm start >"$FRONTEND_LOG" 2>&1 &
  echo $! > "$RUN_DIR/frontend.pid"
)

sleep 2
if ! wait_for_port "${FRONTEND_PORT}" "Frontend"; then
  echo "Frontend failed to start. Check: $FRONTEND_LOG"
  exit 1
fi

echo ""
echo "Services are up:"
echo "Frontend: ${FRONTEND_URL}"
echo "Backend : http://localhost:${BACKEND_PORT}/api/health"
echo ""
echo "PID files:"
echo "  $RUN_DIR/backend.pid"
echo "  $RUN_DIR/frontend.pid"
echo "Logs:"
echo "  $BACKEND_LOG"
echo "  $FRONTEND_LOG"

if command -v open >/dev/null 2>&1; then
  echo ""
  echo "Opening UI: ${FRONTEND_URL}"
  open "${FRONTEND_URL}" >/dev/null 2>&1 || true
fi
