#!/usr/bin/env bash
# Stop the local base model server started by serve_base_model.sh.
set -euo pipefail
MODEL_DIR="${MODEL_DIR:-/home/ubuntu/models}"
PID_FILE="$MODEL_DIR/llama-server.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "no pid file at $PID_FILE; nothing to stop"
  exit 0
fi
PID="$(cat "$PID_FILE")"
if ! kill -0 "$PID" 2>/dev/null; then
  echo "pid $PID not running; removing stale $PID_FILE"
  rm -f "$PID_FILE"
  exit 0
fi
echo "stopping llama-server pid $PID"
kill "$PID"
for _ in $(seq 1 30); do
  kill -0 "$PID" 2>/dev/null || { rm -f "$PID_FILE"; echo "stopped"; exit 0; }
  sleep 1
done
echo "did not exit after SIGTERM; sending SIGKILL"
kill -9 "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
echo "stopped"
