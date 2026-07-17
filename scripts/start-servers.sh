#!/bin/bash
set -e

LLAMA_DIR="$HOME/llama.cpp"
MODELS_DIR="$HOME/parallel-task-engine/models"
BUILD="$LLAMA_DIR/build-arm-optimized"

echo "Starting llama-server instances..."

# Code model (7B) on cores 0-4, port 8001 - used for both code + tests (DAG runs them sequentially)
taskset -c 0-4 "$BUILD/bin/llama-server" \
  -m "$MODELS_DIR/qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
  --port 8001 --metrics -c 8192 --parallel 8 --cont-batching \
  --n-gpu-layers 0 -ngl 0 \
  > ~/parallel-task-engine/logs/server-code.log 2>&1 &
echo "  Code/Tests server (7B) on port 8001, cores 0-4, PID $!"

# Docs model (1.5B) on cores 5-7, port 8002
taskset -c 5-7 "$BUILD/bin/llama-server" \
  -m "$MODELS_DIR/qwen2.5-1.5b-instruct-q4_k_m.gguf" \
  --port 8002 --metrics -c 8192 --parallel 8 --cont-batching \
  --n-gpu-layers 0 -ngl 0 \
  > ~/parallel-task-engine/logs/server-docs.log 2>&1 &
echo "  Docs server (1.5B) on port 8002, cores 5-7, PID $!"

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
echo "Done."
