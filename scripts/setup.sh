#!/bin/bash
set -e

# Parallel Task Decomposition Engine - Setup Script
# Usage: ./setup.sh [--graviton-gen=2|3|4]

GRAVITON_GEN=3

for arg in "$@"; do
    case "$arg" in
        --graviton-gen=*) GRAVITON_GEN="${arg#*=}" ;;
        --help|-h) echo "Usage: $0 [--graviton-gen=2|3|4]" && exit 0 ;;
        *) echo "Unknown option: $arg. Usage: $0 [--graviton-gen=2|3|4]" && exit 1 ;;
    esac
done

case "$GRAVITON_GEN" in
    2|3|4) ;;
    *) echo "Error: graviton-gen must be 2, 3, or 4 (got: $GRAVITON_GEN)" && exit 1 ;;
esac

echo "=== Parallel Task Decomposition Engine Setup ==="
echo "Graviton generation: $GRAVITON_GEN"
echo ""

BASE_DIR="$HOME/parallel-task-engine"
LLAMA_DIR="$HOME/llama.cpp"
MODELS_DIR="$BASE_DIR/models"
BUILD_DIR="$LLAMA_DIR/build-arm-optimized"
LOGS_DIR="$BASE_DIR/logs"

mkdir -p "$MODELS_DIR" "$LOGS_DIR"

install_python_deps() {
    echo "[0/5] Installing Python dependencies..."
    if [ ! -d "$HOME/venv" ]; then
        python3 -m venv "$HOME/venv"
    fi
    source "$HOME/venv/bin/activate"
    pip install --upgrade pip 2>&1 | tail -1
    if [ -f "$BASE_DIR/requirements.txt" ]; then
        pip install -r "$BASE_DIR/requirements.txt" 2>&1 | tail -3
    else
        pip install fastapi uvicorn httpx pydantic psutil 2>&1 | tail -3
    fi
    echo "  Done."
}

setup_llama_build() {
    echo "[1/5] Building Arm-optimized llama.cpp..."
    if [ ! -d "$LLAMA_DIR" ]; then
        git clone https://github.com/ggml-org/llama.cpp "$LLAMA_DIR"
    fi
    cd "$LLAMA_DIR"

    if [ "$GRAVITON_GEN" = "4" ]; then
        ARM_ARCH="armv9-a+sve2+i8mm+dotprod"
    elif [ "$GRAVITON_GEN" = "2" ]; then
        ARM_ARCH="armv8.2-a+dotprod"
    else
        ARM_ARCH="armv8.4-a+dotprod+i8mm"
    fi

    if [ ! -f "$BUILD_DIR/bin/llama-server" ]; then
        cmake -B build-arm-optimized \
            -DGGML_NATIVE=OFF \
            -DGGML_CPU_KLEIDIAI=ON \
            -DGGML_CPU_ARM_ARCH="$ARM_ARCH" \
            -DCMAKE_C_FLAGS="-O3" \
            -DCMAKE_CXX_FLAGS="-O3"
        cmake --build build-arm-optimized --config Release -j$(nproc)
    else
        echo "  Build already exists, skipping."
    fi
    echo "  Done."
}

download_models() {
    echo "[2/5] Downloading models..."
    cd "$MODELS_DIR"

    download_if_missing() {
        local file="$1"
        local repo="$2"
        if [ ! -f "$file" ]; then
            if command -v huggingface-cli &>/dev/null; then
                huggingface-cli download "$repo" "$(basename "$file")" --local-dir . 2>&1 | tail -1
            elif command -v hf &>/dev/null; then
                hf download "$repo" "$(basename "$file")" --local-dir . 2>&1 | tail -1
            else
                echo "  ERROR: Neither 'huggingface-cli' nor 'hf' found. Install huggingface-hub:"
                echo "    pip install huggingface-hub"
                echo "  Then run: huggingface-cli download $repo $(basename $file) --local-dir $MODELS_DIR"
                return 1
            fi
        else
            echo "  $file exists, skipping."
        fi
    }

    download_if_missing "qwen2.5-coder-7b-instruct-q4_k_m.gguf" "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
    download_if_missing "qwen2.5-coder-7b-instruct-q5_k_m.gguf" "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
    download_if_missing "qwen2.5-coder-7b-instruct-q8_0.gguf" "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
    download_if_missing "qwen2.5-1.5b-instruct-q4_k_m.gguf" "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
    download_if_missing "qwen2.5-1.5b-instruct-q5_k_m.gguf" "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
    download_if_missing "qwen2.5-1.5b-instruct-q8_0.gguf" "Qwen/Qwen2.5-1.5B-Instruct-GGUF"

    echo "  Models:"
    ls -lh *.gguf 2>/dev/null | awk '{print "  " $5 " " $NF}'
    echo "  Done."
}

setup_sandbox_user() {
    echo "[3/5] Setting up sandbox user..."
    if ! id -u sandboxuser > /dev/null 2>&1; then
        sudo useradd -M -s /usr/sbin/nologin sandboxuser
        echo "  Created sandboxuser."
    else
        echo "  sandboxuser already exists."
    fi
    echo "  Done."
}

setup_demo_check() {
    cat > /tmp/demo-check.sh << 'DEMOEOF'
#!/bin/bash
echo "=== Demo Pre-flight Check ==="
FAIL=0
for port in 8001 8002; do
    if curl -sf "http://127.0.0.1:$port/health" > /dev/null 2>&1; then
        echo "  llama-server $port: OK"
    else
        echo "  llama-server $port: FAIL"
        FAIL=1
    fi
done
if curl -sf "http://127.0.0.1:9000/health" > /dev/null 2>&1; then
    echo "  API: OK"
else
    echo "  API: FAIL"
    FAIL=1
fi
if curl -sf "http://127.0.0.1:9000/dashboard/dashboard.html" > /dev/null 2>&1; then
    echo "  Dashboard: OK"
else
    echo "  Dashboard: FAIL"
    FAIL=1
fi
echo "=== Result: $([ $FAIL -eq 0 ] && echo 'PASS' || echo 'FAIL') ==="
exit $FAIL
DEMOEOF
    chmod +x /tmp/demo-check.sh
    sudo cp /tmp/demo-check.sh /usr/local/bin/demo-check
    echo "  Created 'demo-check' command."
}

start_servers() {
    echo "[4/5] Starting llama-server instances..."
    kill_existing() {
        pkill -f "llama-server.*port $1" 2>/dev/null || true
    }

    kill_existing 8001
    taskset -c 0-4 "$BUILD_DIR/bin/llama-server" \
        -m "$MODELS_DIR/qwen2.5-coder-7b-instruct-q4_k_m.gguf" \
        --port 8001 --metrics -c 8192 --parallel 8 --cont-batching \
        --n-gpu-layers 0 -ngl 0 \
        > "$LOGS_DIR/server-code.log" 2>&1 &
    echo "  Code (7B) on 8001, cores 0-4, PID $!"

    kill_existing 8002
    taskset -c 5-7 "$BUILD_DIR/bin/llama-server" \
        -m "$MODELS_DIR/qwen2.5-1.5b-instruct-q4_k_m.gguf" \
        --port 8002 --metrics -c 8192 --parallel 8 --cont-batching \
        --n-gpu-layers 0 -ngl 0 \
        > "$LOGS_DIR/server-docs.log" 2>&1 &
    echo "  Docs (1.5B) on 8002, cores 5-7, PID $!"

    echo "  Waiting for servers to load (40s)..."
    sleep 40

    for port in 8001 8002; do
        if curl -sf "http://127.0.0.1:$port/health" > /dev/null 2>&1; then
            echo "  Port $port: HEALTHY"
        else
            echo "  Port $port: NOT READY"
        fi
    done
    echo "  Done."
}

start_api() {
    echo "[5/5] Starting API server..."
    pkill -f "uvicorn backend.main:app" 2>/dev/null || true
    sleep 2

    source "$HOME/venv/bin/activate"
    cd "$BASE_DIR"
    nohup uvicorn backend.main:app --host 0.0.0.0 --port 9000 \
        > "$LOGS_DIR/api.log" 2>&1 &
    echo "  API on port 9000, PID $!"
    sleep 4

    if curl -sf "http://127.0.0.1:9000/health" > /dev/null 2>&1; then
        echo "  API: HEALTHY"
        PUBLIC_IP=$(curl -s http://checkip.amazonaws.com 2>/dev/null || echo 'localhost')
        echo "  Dashboard: http://$PUBLIC_IP:9000/dashboard/dashboard.html"
    else
        echo "  API: NOT READY (check logs/api.log)"
    fi
    echo "  Done."
}

# ---- Main ----
install_python_deps
setup_llama_build
download_models
setup_sandbox_user
setup_demo_check
start_servers
start_api

echo ""
echo "=== Setup Complete ==="
echo "  API:       http://localhost:9000"
echo "  Dashboard: http://localhost:9000/dashboard/dashboard.html"
echo "  Ports:     8001 (7B code), 8002 (1.5B docs)"
echo ""
echo "Run 'demo-check' before presenting."
