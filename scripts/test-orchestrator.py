#!/usr/bin/env python3
"""Test orchestrator with detailed sandbox logging."""
import asyncio
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.orchestrator import Orchestrator


async def main():
    orch = Orchestrator()
    prompt = "Write a Python function to calculate fibonacci numbers. Include unit tests."
    print(f"Prompt: {prompt}")
    result = await orch.execute(prompt)
    for s in result['subtasks']:
        print(f"  [{s['subtask_id']}] {s['name']} - {s['total_duration_ms']:.0f}ms - output_len={len(s['output'])}")
    sb = result.get('sandbox')
    if sb:
        print(f"  Sandbox passed: {sb['passed']}")
        print(f"  Sandbox failure_kind: {sb.get('failure_kind')}")
        print(f"  Sandbox rc: {sb.get('returncode')}")
        print(f"  Sandbox stderr ({len(sb.get('stderr',''))} chars): {sb['stderr'][:300]}")
        print(f"  Sandbox stdout ({len(sb.get('stdout',''))} chars): {sb['stdout'][:200]}")
    else:
        print(f"  No sandbox result!")
    print(f"  Total: {result['total_duration_ms']:.0f}ms")
    print(f"  Verified: {result['fully_verified']}")


if __name__ == "__main__":
    asyncio.run(main())
