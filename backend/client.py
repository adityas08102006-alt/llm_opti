import httpx
import time
import re


def _strip_code_blocks(text: str) -> str:
    blocks = re.findall(r"```(?:python)?\n(.*?)```", text, re.DOTALL)
    if blocks:
        return blocks[0].strip()
    return text.strip()


async def llama_generate(
    port: int,
    prompt: str,
    system: str = "You are a code generation assistant. Output only valid Python code with no explanation.",
    n_predict: int = 512,
    temperature: float = 0.1,
    timeout_secs: int = 120,
) -> dict:
    url = f"http://127.0.0.1:{port}/v1/chat/completions"
    payload = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": n_predict,
    }
    start = time.monotonic()
    async with httpx.AsyncClient(timeout=timeout_secs) as client:
        resp = await client.post(url, json=payload)
    elapsed = time.monotonic() - start
    data = resp.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    timings = data.get("timings", {}) or {}
    usage = data.get("usage", {}) or {}
    return {
        "output": _strip_code_blocks(content),
        "tokens_per_second": timings.get("predicted_per_second", 0) or timings.get("prompt_per_second", 0),
        "timings": timings,
        "total_duration_ms": elapsed * 1000,
        "tokens_generated": usage.get("completion_tokens", timings.get("predicted_n", 0)),
        "tokens_evaluated": usage.get("prompt_tokens", timings.get("prompt_n", 0)),
    }
