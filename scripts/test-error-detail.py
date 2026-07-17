#!/usr/bin/env python3
"""Test endpoint with full error detail."""
import json, urllib.request, traceback

body = json.dumps({"prompt": "Write a function"}).encode()
r = urllib.request.Request("http://127.0.0.1:9000/generate", data=body,
                           headers={"Content-Type": "application/json"})
try:
    resp = json.loads(urllib.request.urlopen(r, timeout=300).read())
    print(json.dumps(resp, indent=2)[:500])
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}")
    print(e.read().decode()[:500])
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
