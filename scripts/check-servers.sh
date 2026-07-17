#!/bin/bash
echo "Health check:"
for port in 8001 8002 8003; do
  if curl -sf "http://127.0.0.1:$port/health" > /dev/null 2>&1; then
    echo "  Port $port: HEALTHY"
  else
    echo "  Port $port: NOT READY"
  fi
done
echo ""
echo "Processes:"
ps aux | grep llama-server | grep -v grep | awk '{print $2, $11, $12}'
