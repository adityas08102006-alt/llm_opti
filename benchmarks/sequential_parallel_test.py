#!/usr/bin/env python3
"""Sequential vs Parallel wall-clock latency test (Step G.1)."""
import asyncio
import time
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.client import llama_generate as generate
from backend.decomposer import extract_code_blocks
from benchmarks.prompts import ALL_PROMPTS

CODE_SYSTEM = "You are a code generation assistant. Output only valid Python code."
TEST_SYSTEM = "You are a test generation assistant. Output only valid Python unittest code."

SAMPLES = 3


async def run_pipeline(prompt: str, port: int, sequential: bool) -> dict:
    start = time.monotonic()

    if sequential:
        code_result = await generate(port, prompt, system=CODE_SYSTEM, n_predict=512, timeout_secs=180)
        docs_result = await generate(8002, f"Write documentation for: {prompt}", n_predict=256, timeout_secs=180)
        test_prompt = f"Write Python unit tests using unittest for this code:\n\n{code_result['output']}"
        test_result = await generate(port, test_prompt, system=TEST_SYSTEM, n_predict=512, timeout_secs=180)
        total = (time.monotonic() - start) * 1000
        return {
            "mode": "sequential", "total_duration_ms": total,
            "code_ms": code_result["total_duration_ms"],
            "docs_ms": docs_result["total_duration_ms"],
            "test_ms": test_result["total_duration_ms"],
        }
    else:
        async def gen_code():
            return await generate(port, prompt, system=CODE_SYSTEM, n_predict=512, timeout_secs=180)
        async def gen_docs():
            return await generate(8002, f"Write documentation for: {prompt}", n_predict=256, timeout_secs=180)
        code_task = asyncio.create_task(gen_code())
        docs_task = asyncio.create_task(gen_docs())
        code_result, docs_result = await asyncio.gather(code_task, docs_task)
        test_prompt = f"Write Python unit tests using unittest for this code:\n\n{code_result['output']}"
        test_result = await generate(port, test_prompt, system=TEST_SYSTEM, n_predict=512, timeout_secs=180)
        total = (time.monotonic() - start) * 1000
        return {
            "mode": "parallel", "total_duration_ms": total,
            "code_ms": code_result["total_duration_ms"],
            "docs_ms": docs_result["total_duration_ms"],
            "test_ms": test_result["total_duration_ms"],
        }


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--output", default="benchmarks/sequential_parallel.json")
    args = parser.parse_args()

    print("=== Sequential vs Parallel Latency (G.1) ===\n")
    results = []

    for tier, prompts in ALL_PROMPTS.items():
        for prompt in prompts[:3]:  # 3 per tier
            for mode in ["sequential", "parallel"]:
                r = await run_pipeline(prompt, args.port, mode == "sequential")
                results.append(r)
                print(f"  {mode:>10} | {tier:>6} | {r['total_duration_ms']/1000:.1f}s | code={r['code_ms']/1000:.1f}s test={r.get('test_ms',0)/1000:.1f}s")
                await asyncio.sleep(2)

    # Aggregate
    by_mode = {"sequential": [], "parallel": []}
    for r in results:
        by_mode[r["mode"]].append(r["total_duration_ms"])

    print(f"\n=== Summary ===")
    for mode in ["sequential", "parallel"]:
        vals = by_mode[mode]
        if vals:
            avg = sum(vals) / len(vals) / 1000
            print(f"  {mode}: avg={avg:.1f}s samples={len(vals)}")

    parallel_vals = by_mode.get("parallel", [])
    seq_vals = by_mode.get("sequential", [])
    if parallel_vals and seq_vals:
        speedup = sum(seq_vals) / len(seq_vals) / (sum(parallel_vals) / len(parallel_vals)) if sum(parallel_vals) > 0 else 0
        print(f"\n  Speedup (parallel vs sequential): {speedup:.2f}x")

    output = {
        "test": "Sequential vs Parallel",
        "results": results,
        "summary": {m: {"avg_s": sum(vals)/len(vals)/1000 if vals else 0, "count": len(vals)} for m, vals in by_mode.items()},
    }
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sequential_parallel.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
