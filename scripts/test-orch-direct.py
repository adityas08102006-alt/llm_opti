#!/usr/bin/env python3
"""Run orchestrator directly to see the full error."""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.orchestrator import Orchestrator

async def main():
    orch = Orchestrator()
    try:
        result = await orch.execute("Write a Python function to calculate fibonacci numbers")
        print("Success!")
        print(f"  shape: {result.get('dag_shape')}")
        print(f"  subtasks: {len(result.get('subtasks', []))}")
        print(f"  sandbox: {result.get('sandbox')}")
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()

asyncio.run(main())
