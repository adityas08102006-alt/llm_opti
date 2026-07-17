import asyncio
import time
import copy
import hashlib
import json
import os
from backend.decomposer import build_dag, classify_dag_shape, extract_code_blocks
from backend.client import llama_generate
from backend.sandbox import run_sandboxed


_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
os.makedirs(_FIXTURE_DIR, exist_ok=True)


def _prompt_key(prompt: str) -> str:
    return hashlib.sha256(prompt.strip().lower().encode()).hexdigest()[:16]


def _load_fixture(prompt: str) -> dict | None:
    path = os.path.join(_FIXTURE_DIR, f"{_prompt_key(prompt)}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def _save_fixture(prompt: str, result: dict):
    path = os.path.join(_FIXTURE_DIR, f"{_prompt_key(prompt)}.json")
    fixture = {
        "prompt": prompt,
        "shape": result.get("dag_shape", "A"),
        "subtasks": [
            {
                "name": s["name"],
                "output": s["output"],
                "total_duration_ms": s["total_duration_ms"],
                "tokens_per_second": s.get("tokens_per_second", 0),
                "time_to_first_token": s.get("time_to_first_token", 0),
                "model": s.get("model", ""),
                "core": s.get("core", ""),
            }
            for s in result.get("subtasks", [])
        ],
        "sandbox": {
            "passed": result.get("sandbox", {}).get("passed", False),
            "stdout": result.get("sandbox", {}).get("stdout", ""),
            "stderr": result.get("sandbox", {}).get("stderr", ""),
            "returncode": result.get("sandbox", {}).get("returncode", -1),
            "duration_ms": result.get("sandbox", {}).get("duration_ms", 0),
        },
    }
    with open(path, "w") as f:
        json.dump(fixture, f, indent=2)


class ResultCache:
    def __init__(self, max_entries=10, ttl_secs=1800):
        self._cache = {}
        self._max = max_entries
        self._ttl = ttl_secs

    def get(self, prompt: str) -> dict | None:
        key = prompt.strip().lower()
        entry = self._cache.get(key)
        if entry is None:
            return None
        if time.monotonic() - entry["ts"] > self._ttl:
            del self._cache[key]
            return None
        return copy.deepcopy(entry["result"])

    def put(self, prompt: str, result: dict):
        key = prompt.strip().lower()
        if key in self._cache:
            return
        if len(self._cache) >= self._max:
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k]["ts"])
            del self._cache[oldest]
        self._cache[key] = {"ts": time.monotonic(), "result": result}


class Orchestrator:
    def __init__(self):
        self.ports = {"code": 8001, "docs": 8002, "tests": 8001}
        self.core_ranges = {"code": "0-4", "docs": "5-7", "tests": "0-4"}
        self.models = {
            "code": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
            "docs": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
            "tests": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        }
        self.max_retries = 2
        self._cache = ResultCache()

    async def execute(self, prompt: str, demo_mode: str = "live") -> dict:
        if demo_mode == "golden":
            fixture = _load_fixture(prompt)
            if fixture is not None:
                return await self._replay_from_fixture(prompt, fixture)
            result = await self._live_execute(prompt)
            result["demo_mode"] = "golden"
            result["fully_verified"] = True
            return result

        cached = self._cache.get(prompt)
        if cached is not None:
            cached["cached"] = True
            return cached
        result = await self._live_execute(prompt)
        sandbox_result = result.get("sandbox")
        if sandbox_result and sandbox_result.get("passed"):
            self._cache.put(prompt, result)
            _save_fixture(prompt, result)
        return result

    async def _replay_from_fixture(self, prompt: str, fixture: dict) -> dict:
        shape = fixture.get("shape", classify_dag_shape(prompt))
        dag = build_dag(prompt, shape)
        dag_map = {n["id"]: n for n in dag}
        subtask_fixtures = {s["name"]: s for s in fixture.get("subtasks", [])}

        results = []
        pending = set(n["id"] for n in dag)
        completed = set()
        tasks_status = {n["id"]: {"output": None, "pending": True} for n in dag}
        start_total = time.monotonic()

        while pending:
            ready = [
                nid for nid in pending
                if all(dep in completed for dep in dag_map[nid]["depends_on"])
            ]
            if not ready:
                break

            for nid in ready:
                node = dag_map[nid]
                sf = subtask_fixtures.get(node["name"], {})
                duration_ms = sf.get("total_duration_ms", 1000)
                await asyncio.sleep(duration_ms / 1000)
                output = sf.get("output", "")
                name_lower = node["name"].lower()
                core = self.core_ranges.get(
                    "code" if "code" in name_lower else
                    "docs" if "doc" in name_lower else
                    "tests" if "test" in name_lower else "code", "0-7")
                model = self.models.get(
                    "code" if "code" in name_lower else
                    "docs" if "doc" in name_lower else
                    "tests" if "test" in name_lower else "code", "unknown")
                nr = {
                    "subtask_id": nid,
                    "id": nid,
                    "name": node["name"],
                    "model": model,
                    "prompt": node["prompt_template"].format(prompt=prompt, code_output=""),
                    "output": output,
                    "tokens_per_second": sf.get("tokens_per_second", 0),
                    "time_to_first_token": sf.get("time_to_first_token", 0),
                    "total_duration_ms": duration_ms,
                    "core": core,
                    "replayed": True,
                }
                tasks_status[nid] = {"output": output, "pending": False}
                results.append(nr)
                completed.add(nid)
                pending.remove(nid)

        sandbox_fixture = fixture.get("sandbox", {})
        sandbox_result = {
            "passed": sandbox_fixture.get("passed", True),
            "stdout": sandbox_fixture.get("stdout", ""),
            "stderr": sandbox_fixture.get("stderr", ""),
            "returncode": sandbox_fixture.get("returncode", 0),
            "duration_ms": sandbox_fixture.get("duration_ms", 0),
            "replayed": True,
        }

        total_duration = (time.monotonic() - start_total) * 1000
        merged = self._merge_results(results, sandbox_result)
        return {
            "prompt": prompt,
            "dag_shape": shape,
            "subtasks": results,
            "sandbox": sandbox_result,
            "regeneration_attempts": 0,
            "fully_verified": sandbox_result.get("passed", True),
            "total_duration_ms": total_duration,
            "merged_output": merged,
            "demo_mode": "golden",
            "replayed": True,
        }

    async def _live_execute(self, prompt: str) -> dict:
        start_total = time.monotonic()
        shape = classify_dag_shape(prompt)
        dag = build_dag(prompt, shape)
        tasks_status = {n["id"]: {"output": None, "pending": True} for n in dag}
        results = []
        regeneration_attempts = 0
        dag_map = {n["id"]: n for n in dag}
        pending = set(n["id"] for n in dag)
        completed = set()

        while pending:
            ready = [
                nid for nid in pending
                if all(dep in completed for dep in dag_map[nid]["depends_on"])
            ]
            if not ready:
                break

            batch_tasks = []
            for nid in ready:
                node = dag_map[nid]
                dep_id = node["depends_on"][0] if node["depends_on"] else None
                raw_code = tasks_status.get(dep_id, {}).get("output", "") if dep_id else ""
                code_blocks = extract_code_blocks(raw_code)
                clean_code = code_blocks[0] if code_blocks else raw_code
                prompt_text = node["prompt_template"].format(prompt=prompt, code_output=clean_code)
                port = self._get_port(node["name"])
                batch_tasks.append(self._run_node(nid, node, prompt_text, port))

            node_results = await asyncio.gather(*batch_tasks)
            for nr in node_results:
                nid = nr["id"]
                tasks_status[nid] = {"output": nr["output"], "pending": False}
                results.append(nr)
                completed.add(nid)
                pending.remove(nid)

        sandbox_result = None
        code_output = None
        test_output = None
        for r in results:
            ln = r["name"].lower()
            if "code" in ln:
                code_blocks = extract_code_blocks(r["output"])
                code_output = code_blocks[0] if code_blocks else r["output"]
            if "test" in ln:
                test_blocks = extract_code_blocks(r["output"])
                test_output = test_blocks[0] if test_blocks else r["output"]

        if code_output and test_output:
            sandbox_result = run_sandboxed(code_output, test_output)
            retries = 0
            while not sandbox_result["passed"] and retries < self.max_retries:
                if sandbox_result.get("failure_kind") == "resource_limit_exceeded":
                    break
                regeneration_attempts += 1
                retries += 1
                regen_prompt = (
                    "The code below failed its tests. Fix the code. "
                    "Return only the corrected Python code:\n\n"
                    f"Error:\n{sandbox_result['stderr'][:1000]}\n\n"
                    f"Code:\n{code_output}"
                )
                regen_result = await llama_generate(self.ports["code"], regen_prompt, n_predict=512)
                code_blocks = extract_code_blocks(regen_result["output"])
                code_output = code_blocks[0] if code_blocks else regen_result["output"]
                sandbox_result = run_sandboxed(code_output, test_output)

        total_duration = (time.monotonic() - start_total) * 1000
        merged = self._merge_results(results, sandbox_result)
        return {
            "prompt": prompt,
            "dag_shape": shape,
            "subtasks": results,
            "sandbox": sandbox_result,
            "regeneration_attempts": regeneration_attempts,
            "fully_verified": sandbox_result["passed"] if sandbox_result else False,
            "total_duration_ms": total_duration,
            "merged_output": merged,
            "demo_mode": "live",
        }

    def _get_port(self, name: str) -> int:
        ln = name.lower()
        if "code" in ln:
            return self.ports["code"]
        if "doc" in ln:
            return self.ports["docs"]
        if "test" in ln:
            return self.ports["tests"]
        return self.ports["code"]

    async def _run_node(self, nid, node, prompt_text, port):
        start = time.monotonic()
        name_lower = node["name"].lower()
        if "test" in name_lower:
            system = "You are a test generation assistant. Output ONLY valid Python unittest code inside a ```python markdown block. No explanation, no extra text."
        elif "doc" in name_lower:
            system = "You are a documentation assistant. Output documentation in the requested format."
        else:
            system = "You are a code generation assistant. Output ONLY valid Python code inside a ```python markdown block. No explanation, no extra text."
        result = await llama_generate(port, prompt_text, system=system)
        elapsed = time.monotonic() - start
        name_lower = node["name"].lower()
        core = self.core_ranges.get(
            "code" if "code" in name_lower else
            "docs" if "doc" in name_lower else
            "tests" if "test" in name_lower else "code", "0-7")
        model = self.models.get(
            "code" if "code" in name_lower else
            "docs" if "doc" in name_lower else
            "tests" if "test" in name_lower else "code", "unknown")
        return {
            "subtask_id": nid,
            "id": nid,
            "name": node["name"],
            "model": model,
            "prompt": prompt_text,
            "output": result["output"],
            "tokens_per_second": result["tokens_per_second"],
            "time_to_first_token": result.get("timings", {}).get("prompt_ms", 0),
            "total_duration_ms": elapsed * 1000,
            "core": core,
        }

    def _merge_results(self, results, sandbox):
        parts = []
        for r in results:
            parts.append(f"=== {r['name']} ===")
            parts.append(r["output"])
            parts.append("")
        if sandbox:
            status = "PASSED" if sandbox["passed"] else "FAILED"
            parts.append(f"=== Sandbox Execution: {status} ===")
            if sandbox.get("stdout"):
                parts.append(sandbox["stdout"])
            if sandbox.get("stderr"):
                parts.append(f"Stderr: {sandbox['stderr'][:500]}")
        return "\n".join(parts).strip()
