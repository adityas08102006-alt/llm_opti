"""Quant level vs sandbox pass-rate benchmark (chat API version)."""
import asyncio
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.client import llama_generate
from backend.sandbox import run_sandboxed
from benchmarks.prompts import ALL_PROMPTS

CODE_SYSTEM = "You are a code generation assistant. Output only valid Python code with no explanation."
TEST_SYSTEM = "You are a test generation assistant. Output only valid Python unittest code with no explanation."


async def run_quant_study(port: int, quant_name: str, output_path: str):
    results = {"quant": quant_name, "results": []}

    for tier, prompts in ALL_PROMPTS.items():
        for i, prompt in enumerate(prompts):
            print(f"  [{quant_name}] {tier} {i+1}/{len(prompts)}: {prompt[:60]}...")

            try:
                code_result = await llama_generate(port, prompt, system=CODE_SYSTEM, n_predict=512, timeout_secs=180)
                code_output = code_result["output"]

                test_prompt = f"Write Python unit tests using unittest for this code:\n\n{code_output}"
                test_result = await llama_generate(port, test_prompt, system=TEST_SYSTEM, n_predict=512, timeout_secs=180)
                test_output = test_result["output"]

                sandbox_result = run_sandboxed(code_output, test_output)

                entry = {
                    "tier": tier,
                    "prompt": prompt,
                    "code_length": len(code_output),
                    "test_length": len(test_output),
                    "code_duration_ms": code_result["total_duration_ms"],
                    "sandbox_passed": sandbox_result["passed"],
                    "sandbox_failure_kind": sandbox_result.get("failure_kind"),
                    "sandbox_stderr": sandbox_result.get("stderr", "")[:200],
                }
                results["results"].append(entry)
                print(f"    code={len(code_output)}c test={len(test_output)}c {'PASS' if sandbox_result['passed'] else 'FAIL'}")

            except Exception as e:
                print(f"    ERROR: {e}")
                results["results"].append({"tier": tier, "prompt": prompt, "error": str(e), "sandbox_passed": False})

            with open(output_path, "w") as f:
                json.dump(results, f, indent=2)

    return results


def summarize(results: dict) -> dict:
    summary = {"quant": results["quant"], "tiers": {}}
    for tier in ["easy", "medium", "hard"]:
        tier_results = [r for r in results["results"] if r.get("tier") == tier and "error" not in r]
        if not tier_results:
            continue
        total = len(tier_results)
        passed = sum(1 for r in tier_results if r["sandbox_passed"])
        avg_dur = sum(r["code_duration_ms"] for r in tier_results) / total if total else 0
        summary["tiers"][tier] = {"total": total, "passed": passed, "pass_rate": round(passed / total * 100, 1), "avg_code_duration_ms": round(avg_dur, 0)}
    all_valid = [r for r in results["results"] if "error" not in r]
    total_pass = sum(1 for r in all_valid if r["sandbox_passed"])
    summary["overall"] = {"total": len(all_valid), "passed": total_pass, "pass_rate": round(total_pass / len(all_valid) * 100, 1) if all_valid else 0}
    return summary


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--quant", default="Q4_K_M")
    parser.add_argument("--output", default="benchmarks/code_quant_study.json")
    args = parser.parse_args()

    print(f"Running code quant study: {args.quant} on port {args.port}")
    results = await run_quant_study(args.port, args.quant, args.output)
    summary = summarize(results)
    print(f"\n=== Summary ({args.quant}) ===")
    print(json.dumps(summary, indent=2))
    print(f"Results saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
