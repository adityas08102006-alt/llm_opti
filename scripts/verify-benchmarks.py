#!/usr/bin/env python3
"""Verify benchmark result files are valid."""
import json, os, sys

benchmarks = os.path.join(os.path.dirname(__file__), "..", "benchmarks")
valid = True

for fname in sorted(os.listdir(benchmarks)):
    if not fname.endswith(".json"):
        continue
    path = os.path.join(benchmarks, fname)
    size = os.path.getsize(path)
    try:
        data = json.load(open(path))
    except Exception as e:
        print(f"FAIL {fname}: invalid JSON ({e})")
        valid = False
        continue

    results = data.get("results", [])
    count = len(results)
    if "quant" in data:
        print(f"OK  {fname}: quant_study, {count} results")
    elif "concurrency" in data.get("results", [{}])[0]:
        print(f"OK  {fname}: concurrent_test, {count} results")
    elif "mode" in data.get("results", [{}])[0]:
        print(f"OK  {fname}: sequential_parallel, {count} results")
    else:
        print(f"OK  {fname}: {count} results (unknown format)")

sys.exit(0 if valid else 1)
