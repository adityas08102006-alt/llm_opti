## Common Commands

### EC2 (Graviton) - SSH Key: `D:\parallel-llm-key.pem`
- SSH: `ssh -i "D:\parallel-llm-key.pem" ubuntu@3.107.210.17`
- SCP: `scp -i "D:\parallel-llm-key.pem" <local> ubuntu@3.107.210.17:<remote>`

### Start Services on EC2
- API: `bash ~/parallel-task-engine/scripts/start-api.sh`
- llama-server: `bash ~/parallel-task-engine/scripts/start-servers.sh`
- Full setup: `bash ~/parallel-task-engine/scripts/setup.sh`

### Verify
- Pre-demo check: `demo-check` (installed at /usr/local/bin/demo-check)
- Arm verification: `bash ~/parallel-task-engine/scripts/verify-arm.sh`

### Backend Structure
- `backend/main.py` — FastAPI app, endpoints
- `backend/orchestrator.py` — DAG executor, golden-path cache
- `backend/decomposer.py` — DAG construction, code extraction
- `backend/client.py` — llama-server HTTP client
- `backend/sandbox.py` — resource-limited subprocess runner
- `backend/metrics.py` — Prometheus metrics scraper
- `backend/scheduler.py` — CPU core monitoring
- `benchmarks/` — Quant study, concurrent throughput, latency comparisons
- `frontend/dashboard.html` — Live dashboard

### Golden-path Cache
- Caches results of verified prompts (max 10, 30 min TTL)
- Cache hit returns result in ~1ms with `"cached": true`

### EC2 Architecture
- Port 8001: Qwen2.5-Coder-7B (cores 0-4)
- Port 8002: Qwen2.5-1.5B (cores 5-7)
- Port 9000: FastAPI + static dashboard
