#!/usr/bin/env python3
"""Quick inference test to verify llama-server is working."""
import json, urllib.request, sys

port = sys.argv[1] if len(sys.argv) > 1 else "8001"
d = json.dumps({"model":"qwen","messages":[{"role":"user","content":"Hello"}],"max_tokens":20}).encode()
r = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions", data=d,
                           headers={"Content-Type":"application/json"})
resp = json.loads(urllib.request.urlopen(r).read())
print(json.dumps(resp, indent=2)[:500])
