# Parallel Task Decomposition Engine

CPU/Arm-optimized multi-model inference platform that decomposes tasks into dependency graphs and runs unblocked subtasks concurrently across CPU cores.

## Two Optimization Axes

1. **Decomposition** — same task, less wall-clock time, by running the right-sized model for each subtask concurrently
2. **Arm-native build** — same model, faster tokens/sec, by compiling llama.cpp with KleidiAI/I8MM microkernels

## Quickstart

```bash
# One-command setup (Graviton3 default)
./scripts/setup.sh

# For Graviton2 (DotProd-only):
./scripts/setup.sh --graviton-gen=2

# For Graviton4 (SVE2):
./scripts/setup.sh --graviton-gen=4
```

## Architecture

```
User Request → Orchestrator → DAG Shape Library → Concurrent Dispatch
                     ↓                                    ↓
              ┌───────┴───────┐                Core 0-4: 7B Code Model
              │               │                Core 5-7: 1.5B Docs Model
              ▼               ▼
         Code (7B)       Docs (1.5B)      ← parallel, independent
              │
              ▼
           Tests (7B)                    ← sequential, depends on code
              │
              ▼
        Sandbox Execution
         (unshare + rlimit)
              │
         ┌────┴────┐
         ▼         ▼
       Pass      Fail (retry ≤2)
         │         │
         └── Merge ─┘
              ↓
        Response + Metrics
```

## Services

| Service | Port | Model | Core Pin |
|---------|------|-------|----------|
| Code + Tests | 8001 | Qwen2.5-Coder-7B Q4_K_M | 0-4 |
| Documentation | 8002 | Qwen2.5-1.5B-Instruct Q4_K_M | 5-7 |
| API | 9000 | — | — |
| Dashboard | 9000/dashboard | — | — |

## Endpoints

- `GET /` — status
- `GET /health` — health check
- `POST /generate` — execute task decomposition
- `GET /dashboard/dashboard.html` — Web UI

## Benchmark Results

### Baseline vs Arm-Optimized (KleidiAI/I8MM)

| Model | Test | Baseline | Arm-Optimized | Delta |
|-------|------|----------|--------------|-------|
| 1.5B Q4_K_M | pp512 | 68.12 t/s | 81.87 t/s | **+20.2%** |
| 1.5B Q4_K_M | tg128 | 7.92 t/s | 8.19 t/s | **+3.4%** |
| 7B Q4_K_M | pp512 | 29.41 t/s | 33.57 t/s | **+14.1%** |
| 7B Q4_K_M | tg128 | 5.05 t/s | 5.23 t/s | **+3.6%** |

### Model Size Matrix

| Model | Q4_K_M | Q5_K_M | Q8_0 |
|-------|--------|--------|------|
| Qwen2.5-Coder-7B | 4.4 GB | 5.1 GB | 7.6 GB |
| Qwen2.5-1.5B | 1.1 GB | 1.2 GB | 1.8 GB |

## Makefile

```bash
make build          # Build both llama.cpp variants
make bench          # Run llama-bench A/B comparison
make download       # Download all model quants
make start          # Start all services
make stop           # Stop all services
make demo-check     # Pre-flight health check
make clean          # Clean build artifacts
```

## Safety — Sandboxed Execution

Generated code is executed with four real isolation mechanisms:

1. **Wall-clock timeout** (10s via `subprocess.run(timeout=10)`)
2. **Network isolation** (`unshare --net` — no network interfaces)
3. **Memory/CPU caps** (`resource.setrlimit` — 512MB AS, 5s CPU)
4. **Unprivileged user** (`sandboxuser` via `sudo -u`)

If `unshare` is restricted by AppArmor, falls back gracefully to `sudo -u sandboxuser`.

## Known Limitations

- DAG shape library is fixed (3 shapes: A/B/C), not a general planner
- Concurrent throughput saturates at ~N=4 on 8 vCPU (core-bound, not software-bound)
- Live demo depends on venue wifi (mitigated by golden-path cache replay)

## Rubric Mapping

| Criterion | Evidence |
|-----------|----------|
| Model size | Quant matrix table |
| Model quality | Sandbox pass-rate study |
| Model speed | llama-bench A/B table |
| Inference server speed | Sequential-vs-parallel chart |
| Developer experience | One-command setup.sh, README, Makefile |
| Arm-specific optimization | KleidiAI/I8MM build flags + Performix profiling |
