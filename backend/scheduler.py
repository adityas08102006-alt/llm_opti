import os
import subprocess


def get_core_count() -> int:
    return os.cpu_count() or 8


def assign_cores(dag: list[dict], total_cores: int) -> dict[int, str]:
    assignments = {}
    n_nodes = len(dag)
    if n_nodes == 0:
        return assignments
    cores_per = max(1, total_cores // n_nodes)
    for i, node in enumerate(dag):
        start = i * cores_per
        end = start + cores_per - 1
        if i == n_nodes - 1:
            end = total_cores - 1
        assignments[node["id"]] = f"{start}-{end}"
    return assignments


def pin_process(pid: int, core_range: str) -> bool:
    try:
        subprocess.run(
            ["taskset", "-p", "-c", core_range, str(pid)],
            check=True, capture_output=True, timeout=5,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_cpu_usage() -> list[float]:
    try:
        import psutil
        return psutil.cpu_percent(interval=0.1, percpu=True)
    except ImportError:
        return []
