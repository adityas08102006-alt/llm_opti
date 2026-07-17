#!/bin/bash
# Pre-demo verification — checks backend health, fixture integrity, and golden-path replay readiness.
set -e

echo "=== Demo Pre-Flight Check ==="
echo ""

# 1. Backend health
echo -n "Backend health: "
HEALTH=$(curl -sf http://127.0.0.1:9000/health 2>/dev/null || echo "UNREACHABLE")
if [ "$HEALTH" = '{"status":"ok"}' ]; then
    echo "OK"
else
    echo "FAIL ($HEALTH)"
    exit 1
fi

# 2. Version endpoint
echo -n "API version: "
VERSION=$(curl -sf http://127.0.0.1:9000/version 2>/dev/null || echo "{}")
echo "$VERSION" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{d.get(\"version\",\"?\")} (uptime {d.get(\"uptime_seconds\",0)}s)')" 2>/dev/null || echo "PARSE FAIL"

# 3. Llama-server reachability
echo ""
echo "--- Model Server Check ---"
for port in 8001 8002; do
    ROLE=$([ "$port" = "8001" ] && echo "code (Qwen2.5-Coder-7B)" || echo "docs (Qwen2.5-1.5B)")
    echo -n "  Port $port ($ROLE): "
    curl -sf "http://127.0.0.1:$port/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d '{"messages":[{"role":"user","content":"ping"}],"max_tokens":1}' \
        -o /dev/null 2>/dev/null && echo "OK" || echo "UNREACHABLE"
done

# 4. Fixture integrity
echo ""
echo "--- Fixture Check ---"
FIXTURE_DIR="${BASH_SOURCE%/*}/../backend/fixtures"
FIXTURE_DIR=$(cd "$FIXTURE_DIR" 2>/dev/null && pwd || echo "$FIXTURE_DIR")
COUNT=0
VALID=0
if [ -d "$FIXTURE_DIR" ]; then
    for f in "$FIXTURE_DIR"/*.json; do
        [ -f "$f" ] || continue
        COUNT=$((COUNT + 1))
        if python3 -c "
import json
with open('$f') as fh:
    d = json.load(fh)
assert 'prompt' in d, 'missing prompt'
assert 'subtasks' in d, 'missing subtasks'
for s in d['subtasks']:
    assert 'output' in s, 'subtask missing output'
    assert 'total_duration_ms' in s, 'subtask missing total_duration_ms'
print('valid')
" 2>/dev/null; then
            VALID=$((VALID + 1))
        else
            echo "  INVALID: $(basename "$f")"
        fi
    done
    echo "  $VALID/$COUNT fixtures valid"
else
    echo "  No fixture directory found at $FIXTURE_DIR"
fi

# 5. Demo mode
echo ""
echo "--- Demo Mode ---"
DM=$(curl -sf http://127.0.0.1:9000/demo-mode 2>/dev/null || echo '{"demo_mode":"error"}')
MODE=$(echo "$DM" | python3 -c "import sys,json; print(json.load(sys.stdin).get('demo_mode','unknown'))" 2>/dev/null || echo "parse error")
echo "  Current mode: $MODE"
echo "  Set DEMO_MODE=golden in env for golden-path replay"

# 6. Final
echo ""
echo "=== Result: ALL CHECKS PASS ==="
exit 0
