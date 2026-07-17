#!/bin/bash
LLAMA_DIR="$HOME/llama.cpp"
MODELS_DIR="$HOME/parallel-task-engine/models"
BUILD="$LLAMA_DIR/build-arm-optimized"
LOG_DIR="$HOME/parallel-task-engine/logs"
mkdir -p "$LOG_DIR"

pkill -f "llama-server.*port 8001" 2>/dev/null || true
pkill -f "llama-server.*port 8002" 2>/dev/null || true
sleep 2

echo "Starting llama-server instances..."

# Code model (7B) — reduced ctx/parallel to fit Graviton memory
taskset -c 0-4 "$BUILD/bin/llama-server" \
  -m "$MODELS_DIR/qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
  --port 8001 --metrics -c 4096 --parallel 4 --cont-batching \
  --n-gpu-layers 0 -ngl 0 \
  > "$LOG_DIR/server-code.log" 2>&1 &
CODE_PID=$!
echo "  Code/Tests server (7B) on port 8001, cores 0-4, PID $CODE_PID"

# Docs model (1.5B)
taskset -c 5-7 "$BUILD/bin/llama-server" \
  -m "$MODELS_DIR/qwen2.5-1.5b-instruct-q4_k_m.gguf" \
  --port 8002 --metrics -c 4096 --parallel 4 --cont-batching \
  --n-gpu-layers 0 -ngl 0 \
  > "$LOG_DIR/server-docs.log" 2>&1 &
DOCS_PID=$!
echo "  Docs server (1.5B) on port 8002, cores 5-7, PID $DOCS_PID"

echo "Waiting for servers to load..."
sleep 20

echo "Health checks:"
for port in 8001 8002; do
  if curl -sf "http://127.0.0.1:$port/health" > /dev/null 2>&1; then
    echo "  Port $port: HEALTHY"
  else
    echo "  Port $port: NOT READY"
  fi
done

# Watchdog: restart 7B if it crashes
(
  while true; do
    sleep 30
    if ! kill -0 $CODE_PID 2>/dev/null; then
      echo "$(date) 7B server (PID $CODE_PID) died, restarting..." >> "$LOG_DIR/watchdog.log"
      taskset -c 0-4 "$BUILD/bin/llama-server" \
        -m "$MODELS_DIR/qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
        --port 8001 --metrics -c 4096 --parallel 4 --cont-batching \
        --n-gpu-layers 0 -ngl 0 \
        > "$LOG_DIR/server-code.log" 2>&1 &
      CODE_PID=$!
      echo "  Restarted 7B server with PID $CODE_PID"
      sleep 20
    fi
  done
) &
echo "  Watchdog started (PID $!)"

echo "Done."
