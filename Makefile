.PHONY: build build-baseline build-arm bench download start stop demo-check clean

LLAMA_DIR = $(HOME)/llama.cpp
MODELS_DIR = $(HOME)/parallel-task-engine/models
BUILD_DIR = $(LLAMA_DIR)/build-arm-optimized
BASELINE_DIR = $(LLAMA_DIR)/build-baseline

build: build-baseline build-arm

build-baseline:
	cd $(LLAMA_DIR) && cmake -B build-baseline && cmake --build build-baseline --config Release -j$$(nproc)

build-arm:
	cd $(LLAMA_DIR) && cmake -B build-arm-optimized \
		-DGGML_NATIVE=OFF -DGGML_CPU_KLEIDIAI=ON \
		-DGGML_CPU_ARM_ARCH=armv8.4-a+dotprod+i8mm \
		-DCMAKE_C_FLAGS="-O3" -DCMAKE_CXX_FLAGS="-O3" && \
		cmake --build build-arm-optimized --config Release -j$$(nproc)

bench:
	@echo "=== Baseline ==="
	$(BASELINE_DIR)/bin/llama-bench -m $(MODELS_DIR)/qwen2.5-1.5b-instruct-q4_k_m.gguf -p 512 -n 128 -t 8
	@echo "=== Arm-Optimized ==="
	$(BUILD_DIR)/bin/llama-bench -m $(MODELS_DIR)/qwen2.5-1.5b-instruct-q4_k_m.gguf -p 512 -n 128 -t 8

download:
	cd $(MODELS_DIR) && \
	hf download Qwen/Qwen2.5-Coder-7B-Instruct-GGUF --local-dir . 2>/dev/null; \
	hf download Qwen/Qwen2.5-1.5B-Instruct-GGUF --local-dir . 2>/dev/null

start:
	cd $(HOME)/parallel-task-engine && bash scripts/start-servers.sh
	source $(HOME)/venv/bin/activate && cd $(HOME)/parallel-task-engine && \
		nohup uvicorn backend.main:app --host 0.0.0.0 --port 9000 --workers 4 > logs/api.log 2>&1 &

stop:
	pkill -f "llama-server.*port 8001" 2>/dev/null || true
	pkill -f "llama-server.*port 8002" 2>/dev/null || true
	pkill -f "uvicorn backend.main:app" 2>/dev/null || true

demo-check:
	@echo "=== Pre-flight Check ==="; \
	fail=0; \
	for port in 8001 8002; do \
		curl -sf http://127.0.0.1:$$port/health > /dev/null 2>&1 && \
			echo "  llama-server $$port: OK" || { echo "  llama-server $$port: FAIL"; fail=1; }; \
	done; \
	curl -sf http://127.0.0.1:9000/health > /dev/null 2>&1 && \
		echo "  API: OK" || { echo "  API: FAIL"; fail=1; }; \
	[ $$fail -eq 0 ] && echo "=== PASS ===" || echo "=== FAIL ==="

clean:
	rm -rf $(BASELINE_DIR) $(BUILD_DIR)
