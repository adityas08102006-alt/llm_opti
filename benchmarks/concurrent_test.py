#!/usr/bin/env python3
"""Concurrent request throughput test (Step G.5)."""
import asyncio
import httpx
import time
import statistics
import json
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_URL = "http://127.0.0.1:9000/generate"
TEST_PROMPT = "Write a Python function to calculate fibonacci numbers."
CONCURRENCY_LEVELS = [1, 2, 4, 8]
REQUESTS_PER_LEVEL = 3


async def send_request(client, prompt, idx):
    start = time.monotonic()
    try:
        resp = await client.post(API_URL, json={"prompt": prompt}, timeout=300)
        elapsed = time.monotonic() - start
        data = resp.json()
        return {
            "idx": idx,
            "status": resp.status_code,
            "duration_ms": elapsed * 1000,
            "duration_s": round(elapsed, 2),
            "verified": data.get("fully_verified", False),
            "subtask_count": len(data.get("subtasks", [])),
            "error": None,
        }
    except Exception as e:
        elapsed = time.monotonic() - start
        return {"idx": idx, "status": 0, "duration_ms": elapsed * 1000, "duration_s": round(elapsed, 2), "verified": False, "error": str(e)}


async def run_concurrency_test(n: int) -> dict:
    print(f"  Testing N={n} concurrent requests...")
    async with httpx.AsyncClient(timeout=300) as client:
        tasks = [send_request(client, TEST_PROMPT, i) for i in range(n)]
        start = time.monotonic()
        results = await asyncio.gather(*tasks)
        total_elapsed = time.monotonic() - start

    durations = [r["duration_ms"] for r in results if r["error"] is None]
    all_durations = [r["duration_ms"] for r in results]

    # Detect serialization: if max ≈ sum of all individual durations, requests are serialized
    total_individual = sum(durations) if durations else 0
    serialization_ratio = round(total_individual / max(total_elapsed * 1000, 1), 2)

    return {
        "concurrency": n,
        "total_requests": n,
        "total_elapsed_s": round(total_elapsed, 2),
        "throughput_req_per_s": round(n / total_elapsed, 2) if total_elapsed > 0 else 0,
        "p50_ms": round(statistics.median(durations), 0) if durations else 0,
        "p95_ms": round(sorted(durations)[int(len(durations) * 0.95) - 1], 0) if len(durations) >= 2 else 0,
        "min_ms": round(min(all_durations), 0) if all_durations else 0,
        "max_ms": round(max(all_durations), 0) if all_durations else 0,
        "verified_count": sum(1 for r in results if r["verified"]),
        "error_count": sum(1 for r in results if r["error"]),
        "serialization_ratio": serialization_ratio,
        "results": results,
    }


async def main():
    print("=== Concurrent Request Throughput Test (G.5) ===\n")
    all_results = []

    for n in CONCURRENCY_LEVELS:
        for _ in range(REQUESTS_PER_LEVEL):
            result = await run_concurrency_test(n)
            all_results.append(result)
            # Brief cooldown between levels
            await asyncio.sleep(5)

    # Aggregate by concurrency level
    by_level = {}
    for r in all_results:
        n = r["concurrency"]
        if n not in by_level:
            by_level[n] = []
        by_level[n].append(r)

    print("\n=== Summary ===")
    print(f"{'N':>4} | {'Throughput':>10} | {'p50(ms)':>8} | {'p95(ms)':>8} | {'Min(ms)':>8} | {'Max(ms)':>8} | {'SerRatio':>8} | {'Verified':>8}")
    print("-" * 85)
    for n in CONCURRENCY_LEVELS:
        rows = by_level.get(n, [])
        if not rows:
            continue
        avg_tp = statistics.mean(r["throughput_req_per_s"] for r in rows)
        avg_p50 = statistics.mean(r["p50_ms"] for r in rows)
        avg_p95 = statistics.mean(r["p95_ms"] for r in rows)
        avg_min = statistics.mean(r["min_ms"] for r in rows)
        avg_max = statistics.mean(r["max_ms"] for r in rows)
        avg_ser = statistics.mean(r["serialization_ratio"] for r in rows)
        avg_ver = statistics.mean(r["verified_count"] for r in rows)
        print(f"{n:>4} | {avg_tp:>8.2f} req/s | {avg_p50:>8.0f} | {avg_p95:>8.0f} | {avg_min:>8.0f} | {avg_max:>8.0f} | {avg_ser:>8.1f}x | {avg_ver:>8.1f}")
    print("\n  Serialization Ratio = sum(individual durations) / wall-clock overlap")
    print("  Ratio ≈ 1.0 → fully serialized (bottleneck at API worker)")
    print("  Ratio ≈ N   → fully parallel (linear scaling)")

    output = {"test": "Concurrent Throughput", "prompt": TEST_PROMPT, "results": all_results}
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "concurrent_throughput.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
