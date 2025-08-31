#!/usr/bin/env bash
set -euo pipefail

# Start API
uvicorn "text2audio.api:app" --host 0.0.0.0 --port 8000 &
API_PID=$!

# Start UI
streamlit run text2audio/web_app.py --server.port 8501 --server.address 0.0.0.0 &
UI_PID=$!

term_handler() {
  kill -TERM "$API_PID" "$UI_PID" 2>/dev/null || true
  wait "$API_PID" "$UI_PID" 2>/dev/null || true
}
trap term_handler SIGTERM SIGINT

wait -n "$API_PID" "$UI_PID" || true
kill -TERM "$API_PID" "$UI_PID" 2>/dev/null || true
wait || true
