#!/usr/bin/env python3
"""Test the golden-path cache by running the same prompt twice."""
import json, urllib.request, time, sys

body = json.dumps({"prompt": "Write a Python function to calculate fibonacci numbers with unit tests"}).encode()

# First run
print("=== First request ===")
r = urllib.request.Request("http://127.0.0.1:9000/generate", data=body,
                           headers={"Content-Type": "application/json"})
try:
    t0 = time.monotonic()
    resp = json.loads(urllib.request.urlopen(r, timeout=300).read())
    t1 = time.monotonic()
    print(f"  shape: {resp.get('dag_shape')}")
    print(f"  subtasks: {len(resp.get('subtasks', []))}")
    print(f"  verified: {resp.get('fully_verified')}")
    print(f"  cached: {resp.get('cached', False)}")
    print(f"  duration: {(t1-t0)*1000:.0f}ms")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code}: {e.read().decode()[:300]}")

# Second run - should be cached
print("\n=== Second request (should cache-hit) ===")
r2 = urllib.request.Request("http://127.0.0.1:9000/generate", data=body,
                            headers={"Content-Type": "application/json"})
try:
    t0 = time.monotonic()
    resp2 = json.loads(urllib.request.urlopen(r2, timeout=30).read())
    t1 = time.monotonic()
    print(f"  shape: {resp2.get('dag_shape')}")
    print(f"  subtasks: {len(resp2.get('subtasks', []))}")
    print(f"  verified: {resp2.get('fully_verified')}")
    print(f"  cached: {resp2.get('cached', False)}")
    print(f"  duration: {(t1-t0)*1000:.0f}ms")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code}: {e.read().decode()[:300]}")
