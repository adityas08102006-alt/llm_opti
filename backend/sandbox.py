import resource
import subprocess
import time
import os

SANDBOX_RLIMIT_AS = 256 * 1024 * 1024
SANDBOX_CPU_TIME = 10
SANDBOX_WALL_TIME = 20
SANDBOX_USER = "sandboxuser"


def _limit_resources():
    resource.setrlimit(resource.RLIMIT_AS, (SANDBOX_RLIMIT_AS,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (SANDBOX_CPU_TIME,) * 2)


def _classify_failure(result: subprocess.CompletedProcess) -> str:
    stderr = (result.stderr or b"").decode(errors="replace")
    if result.returncode == -9 or "MemoryError" in stderr or "Cannot allocate memory" in stderr:
        return "resource_limit_exceeded"
    if result.returncode == -6:
        return "cpu_time_exceeded"
    if result.returncode == -15:
        return "wall_timeout"
    return "test_failed"


def run_sandboxed(code: str, test_code: str) -> dict:
    combined = f"{code}\n\n{test_code}"
    start = time.monotonic()

    exists = (
        subprocess.run(["id", "-u", SANDBOX_USER], capture_output=True, timeout=5).returncode == 0
    )
    if not exists:
        subprocess.run(
            ["sudo", "useradd", "-M", "-s", "/usr/sbin/nologin", SANDBOX_USER],
            capture_output=True, timeout=10,
        )

    unshare_worked = False
    try:
        result = subprocess.run(
            ["sudo", "-u", SANDBOX_USER, "unshare", "--net", "--map-root-user", "--",
             "python3", "-c", combined],
            timeout=SANDBOX_WALL_TIME,
            capture_output=True,
            preexec_fn=_limit_resources,
        )
        stderr_text = (result.stderr or b"").decode(errors="replace")
        if "Operation not permitted" in stderr_text or "denied" in stderr_text.lower():
            raise PermissionError(stderr_text[:200])
        unshare_worked = result.returncode == 0
    except (FileNotFoundError, PermissionError, subprocess.SubprocessError):
        result = subprocess.run(
            ["sudo", "-u", SANDBOX_USER, "python3", "-c", combined],
            timeout=SANDBOX_WALL_TIME,
            capture_output=True,
            preexec_fn=_limit_resources,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        return {
            "passed": False,
            "stdout": "",
            "stderr": "Wall timeout expired",
            "returncode": -15,
            "failure_kind": "wall_timeout",
            "duration_ms": elapsed * 1000,
            "unshare_active": False,
        }

    elapsed = time.monotonic() - start
    failure_kind = None
    if result.returncode != 0:
        failure_kind = _classify_failure(result)

    return {
        "passed": result.returncode == 0,
        "stdout": result.stdout.decode(errors="replace") if result.stdout else "",
        "stderr": result.stderr.decode(errors="replace") if result.stderr else "",
        "returncode": result.returncode,
        "failure_kind": failure_kind,
        "duration_ms": elapsed * 1000,
        "unshare_active": unshare_worked,
    }
