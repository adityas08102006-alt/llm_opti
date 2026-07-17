import asyncio
import json
import os
import sys
import time
import uuid
from collections import deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from starlette.responses import JSONResponse
from backend.models import PromptRequest
from backend.orchestrator import Orchestrator
from backend.metrics import MetricsCollector
from backend.scheduler import get_cpu_usage


class LiveStats:
    def __init__(self):
        self.llama_metrics = {}
        self.cpu_percent = []
        self.timestamps = deque(maxlen=300)
        self.last_generate_duration = 0
        self.total_requests = 0
        self.sandbox_passes = 0
        self.sandbox_fails = 0


stats = LiveStats()
metrics_collector = MetricsCollector()
orchestrator = Orchestrator()


async def background_collector():
    while True:
        try:
            stats.llama_metrics = await metrics_collector.scrape_all()
            stats.cpu_percent = get_cpu_usage()
            stats.timestamps.append(time.time())
        except Exception:
            pass
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    collector = asyncio.create_task(background_collector())
    cleaner = asyncio.create_task(_task_cleanup())
    yield
    collector.cancel()
    cleaner.cancel()


app = FastAPI(title="Parallel Task Decomposition Engine", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=str(frontend_dir), html=True), name="dashboard")

API_KEY = os.environ.get("API_KEY", "")

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path in ("/health", "/", "/version") or path.startswith(("/dashboard", "/docs", "/openapi")):
        return await call_next(request)
    if not API_KEY:
        return await call_next(request)
    auth = request.headers.get("Authorization", "")
    if auth == f"Bearer {API_KEY}":
        return await call_next(request)
    return JSONResponse(status_code=401, content={"detail": "Unauthorized"})


@app.get("/")
def home():
    return {"status": "running", "version": "2.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


_server_start = time.monotonic()


@app.get("/version")
def version():
    build = check_kleidiai_build()
    return {
        "version": app.version,
        "models": [
            {"name": orchestrator.models["code"], "port": orchestrator.ports["code"], "role": "code"},
            {"name": orchestrator.models["docs"], "port": orchestrator.ports["docs"], "role": "docs"},
        ],
        "kleidiai": {"enabled": build["kleidiai_build"], "arm_arch": build["arm_arch"]},
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "uptime_seconds": int(time.monotonic() - _server_start),
    }


arm_build_dir = Path.home() / "llama.cpp" / "build-arm-optimized"

def check_arm_features() -> dict:
    features = {"neon": False, "dotprod": False, "i8mm": False, "sve": False}
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("Features"):
                    feats = line.split(":")[1].strip().split()
                    features["neon"] = "asimd" in feats
                    features["dotprod"] = "asimddp" in feats
                    features["i8mm"] = "i8mm" in feats
                    features["sve"] = "sve" in feats
                    break
    except OSError:
        features = {"neon": None, "dotprod": None, "i8mm": None, "sve": None}
    return features


def check_kleidiai_build() -> dict:
    info = {"kleidiai_build": False, "arm_arch": None}
    cmake = arm_build_dir / "CMakeCache.txt"
    if cmake.exists():
        text = cmake.read_text()
        info["kleidiai_build"] = "GGML_CPU_KLEIDIAI:BOOL=ON" in text
        for line in text.splitlines():
            if line.startswith("GGML_CPU_ARM_ARCH:"):
                info["arm_arch"] = line.split("=", 1)[1]
                break
    return info


@app.get("/system/arm-verify")
def arm_verify():
    cpu = check_arm_features()
    build = check_kleidiai_build()
    all_pass = all(cpu.values()) and build.get("kleidiai_build") if cpu else False
    return {"status": "pass" if all_pass else "warn", **cpu, **build}


@app.get("/stats")
def get_stats():
    return {
        "llama_metrics": stats.llama_metrics,
        "cpu_percent": stats.cpu_percent,
        "total_requests": stats.total_requests,
        "sandbox_passes": stats.sandbox_passes,
        "sandbox_fails": stats.sandbox_fails,
        "last_generate_duration_ms": stats.last_generate_duration,
    }


@app.get("/demo-mode")
def get_demo_mode():
    return {"demo_mode": os.environ.get("DEMO_MODE", "live")}


# ---------- async task store (file-based, shared across uvicorn workers) ----------
_TASK_DIR = "/tmp/llm-tasks"
os.makedirs(_TASK_DIR, exist_ok=True)


def _task_path(task_id: str) -> str:
    return os.path.join(_TASK_DIR, f"{task_id}.json")


def _write_task(task_id: str, data: dict):
    tmp = _task_path(task_id) + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, _task_path(task_id))


def _read_task(task_id: str) -> dict | None:
    path = _task_path(task_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


async def _task_cleanup():
    """Remove tasks older than 30 minutes every 5 minutes."""
    while True:
        try:
            now = time.time()
            for fname in os.listdir(_TASK_DIR):
                fpath = os.path.join(_TASK_DIR, fname)
                if fname.endswith(".json") and now - os.path.getmtime(fpath) > 1800:
                    os.remove(fpath)
        except OSError:
            pass
        await asyncio.sleep(300)


@app.post("/generate")
async def generate(request: PromptRequest):
    try:
        start = time.monotonic()
        result = await orchestrator.execute(request.prompt, demo_mode=request.demo_mode)
        elapsed = (time.monotonic() - start) * 1000
        stats.last_generate_duration = elapsed
        stats.total_requests += 1
        sb = result.get("sandbox")
        if sb:
            if sb.get("passed"):
                stats.sandbox_passes += 1
            else:
                stats.sandbox_fails += 1
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks")
async def create_task(request: PromptRequest):
    task_id = uuid.uuid4().hex[:12]
    _write_task(task_id, {"status": "running", "result": None, "created_at": time.time(), "prompt": request.prompt, "demo_mode": request.demo_mode})

    async def _run():
        try:
            entry = _read_task(task_id)
            result = await orchestrator.execute(request.prompt, demo_mode=request.demo_mode)
            _write_task(task_id, {"status": "completed", "result": result, "created_at": entry["created_at"]})
        except Exception as e:
            entry = _read_task(task_id)
            _write_task(task_id, {"status": "failed", "error": str(e), "created_at": entry["created_at"] if entry else 0})

    asyncio.create_task(_run())
    return {"task_id": task_id, "status": "running"}


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    entry = _read_task(task_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if entry["status"] == "completed":
        result = entry.get("result")
        if result:
            stats.total_requests += 1
            sb = result.get("sandbox")
            if sb:
                if sb.get("passed"):
                    stats.sandbox_passes += 1
                else:
                    stats.sandbox_fails += 1
        return {"status": "completed", "result": result}
    if entry["status"] == "failed":
        return {"status": "failed", "error": entry.get("error", "Unknown error")}
    return {"status": "running"}
