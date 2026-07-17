#!/bin/bash
cd /home/ubuntu/parallel-task-engine
pkill -f 'uvicorn backend.main:app' 2>/dev/null
sleep 1
if [ -f .env ]; then
  set -a; source .env; set +a
fi
exec nohup /home/ubuntu/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 9000 > /home/ubuntu/parallel-task-engine/logs/api.log 2>&1 &
disown
sleep 5
curl -sf http://127.0.0.1:9000/health && echo "API OK" || echo "API FAIL"
