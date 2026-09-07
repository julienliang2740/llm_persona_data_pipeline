#!/usr/bin/env bash
# Start the local base model (llama.cpp llama-server, OpenAI-compatible) in the background.
# Idempotent: if a server is already listening on $PORT, this reports it and exits 0.
# The pipeline points at it with base_url http://127.0.0.1:8080/v1 (no API key needed).
set -euo pipefail

LLAMA_DIR="${LLAMA_DIR:-/home/ubuntu/tools/llama.cpp}"
MODEL_DIR="${MODEL_DIR:-/home/ubuntu/models}"
MODEL_PATH="${MODEL_PATH:-$MODEL_DIR/Qwen2.5-7B-Instruct-Q4_K_M.gguf}"
MODEL_ALIAS="${MODEL_ALIAS:-qwen2.5-7b-instruct}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8080}"
THREADS="${THREADS:-8}"
PARALLEL="${PARALLEL:-4}"          # concurrent slots
CTX_PER_SLOT="${CTX_PER_SLOT:-4096}"
CTX_TOTAL=$(( CTX_PER_SLOT * PARALLEL ))   # llama-server splits -c across slots

PID_FILE="$MODEL_DIR/llama-server.pid"
LOG_FILE="$MODEL_DIR/llama-server.log"

if curl -sf --max-time 2 "http://$HOST:$PORT/health" >/dev/null 2>&1; then
  echo "llama-server already running and healthy on $HOST:$PORT (pid $(cat "$PID_FILE" 2>/dev/null || echo '?'))"
  exit 0
fi

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "llama-server process $(cat "$PID_FILE") is alive but not answering /health yet; tail $LOG_FILE"
  exit 0
fi

[ -f "$MODEL_PATH" ] || { echo "model file not found: $MODEL_PATH" >&2; exit 1; }
[ -x "$LLAMA_DIR/llama-server" ] || { echo "llama-server not found in $LLAMA_DIR" >&2; exit 1; }

echo "starting llama-server: $MODEL_PATH (threads=$THREADS parallel=$PARALLEL ctx_total=$CTX_TOTAL)"
# --load-mode none reads the weights into anonymous RAM instead of mmap'ing the file.
# This box has no swap, and RLIMIT_MEMLOCK (~3.85 GB) is below the 4.37 GB model, so full mlock
# is impossible. Anonymous pages cannot be evicted; mmap'd file pages can be, and eviction showed
# up in benchmarks as sudden ~8x decode slowdowns. Costs a slower start, buys stable throughput.
LD_LIBRARY_PATH="$LLAMA_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
nohup "$LLAMA_DIR/llama-server" \
  --model "$MODEL_PATH" \
  --alias "$MODEL_ALIAS" \
  --host "$HOST" --port "$PORT" \
  --threads "$THREADS" --threads-batch "$THREADS" \
  --ctx-size "$CTX_TOTAL" \
  --parallel "$PARALLEL" \
  --batch-size 2048 --ubatch-size 512 \
  --load-mode none \
  --cont-batching \
  --no-webui \
  >"$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
echo "pid $(cat "$PID_FILE") -> $LOG_FILE ; waiting for /health ..."

for _ in $(seq 1 180); do
  if curl -sf --max-time 2 "http://$HOST:$PORT/health" >/dev/null 2>&1; then
    echo "ready: http://$HOST:$PORT/v1 (model id: $MODEL_ALIAS)"
    exit 0
  fi
  kill -0 "$(cat "$PID_FILE")" 2>/dev/null || { echo "server died during startup; see $LOG_FILE" >&2; exit 1; }
  sleep 1
done
echo "timed out waiting for /health; see $LOG_FILE" >&2
exit 1
