#!/usr/bin/env python3
"""Quick orchestrator end-to-end test."""
import sys, os, json, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

prompt = "Write a Python function to calculate fibonacci numbers and unit tests"
body = json.dumps({"prompt": prompt}).encode()
r = urllib.request.Request("http://127.0.0.1:9000/generate", data=body,
                           headers={"Content-Type": "application/json"})
resp = json.loads(urllib.request.urlopen(r, timeout=300).read())
print(f"shape: {resp.get('dag_shape')}")
print(f"subtasks: {len(resp.get('subtasks', []))}")
print(f"verified: {resp.get('fully_verified')}")
print(f"total_s: {resp.get('total_duration_ms', 0)/1000:.1f}")
print(f"regen: {resp.get('regeneration_attempts')}")
for s in resp.get("subtasks", []):
    print(f"  [{s['subtask_id']}] {s['name']} - {s['total_duration_ms']:.0f}ms")
