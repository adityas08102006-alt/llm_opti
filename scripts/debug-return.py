#!/usr/bin/env python3
"""Check the full execute method source."""
import sys, os, inspect
sys.path.insert(0, "/home/ubuntu/parallel-task-engine")
import backend.orchestrator as o
src = inspect.getsource(o.Orchestrator.execute)
lines = src.split("\n")
for i, line in enumerate(lines[115:], start=116):
    if "return" in line:
        print(f"{i:3d}: {line}")
