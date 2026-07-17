import httpx
from collections import deque


class MetricsCollector:
    def __init__(self):
        self.llama_ports = [8001, 8002, 8003]
        self.history = deque(maxlen=300)

    async def scrape_all(self) -> dict:
        results = {}
        for port in self.llama_ports:
            try:
                metrics = await self._scrape_metrics(port)
                results[port] = metrics
            except Exception as e:
                results[port] = {"error": str(e)}
        return results

    async def _scrape_metrics(self, port: int) -> dict:
        url = f"http://127.0.0.1:{port}/metrics"
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url)
        text = resp.text
        metrics = {}
        for line in text.split("\n"):
            if line.startswith("llamacpp:"):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        key = parts[0].split("{")[0]
                        val = float(parts[-1])
                        if val > 0:
                            metrics[key] = val
                    except ValueError:
                        pass
        return metrics

    def aggregate(self, snapshot: dict) -> dict:
        agg = {
            "total_prompt_tokens_per_second": 0,
            "total_predicted_tokens_per_second": 0,
        }
        for port, data in snapshot.items():
            if isinstance(data, dict) and "error" not in data:
                pps = data.get("llamacpp:prompt_tokens_seconds", 0)
                tgs = data.get("llamacpp:predicted_tokens_seconds", 0)
                if pps:
                    agg["total_prompt_tokens_per_second"] += 1.0 / pps
                if tgs:
                    agg["total_predicted_tokens_per_second"] += 1.0 / tgs
        return agg
