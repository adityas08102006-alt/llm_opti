#!/usr/bin/env python3
"""Debug orchestrator None return."""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import backend.orchestrator as orch_mod
import inspect

# Check if the result variable is in the execute function
src = inspect.getsource(orch_mod.Orchestrator.execute)
print("=== execute() source ===")
print(src[:2000])
print("...")
