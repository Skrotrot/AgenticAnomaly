import asyncio
import json
import logging
import os
from json import JSONDecodeError
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status

from agent import SOCAgent


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("agentic-soc-benchmark")

app = FastAPI(title="Agentic SOC benchmark")
benchmark_lock = asyncio.Lock()

NUMBER_OF_RUNS = 10
MAX_CONCURRENCY = 10
MODELS = [
    "openrouter:qwen/qwen3-vl-235b-a22b-instruct",
    "openrouter:openai/gpt-oss-120b:nitro",
    "openrouter:anthropic/claude-haiku-4.5",
    "openrouter:deepseek/deepseek-v4-flash",
]
PROMPTS = [""]


async def run_case(model: str, prompt: str, prompt_index: int, evidence: str) -> tuple[str, dict[str, int]]:
    soc_agent = SOCAgent(model=model, prompt=prompt)
    await soc_agent.batch_investigate(
        evidence,
        runs=NUMBER_OF_RUNS,
        max_concurrency=MAX_CONCURRENCY,
    )
    return (
        f"{model}::prompt_{prompt_index}",
        {"revoked": soc_agent.times_revoked},
    )


async def benchmark(payload: Any) -> dict[str, dict[str, int]]:
    evidence = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    tasks = [
        run_case(model, prompt, prompt_index, evidence)
        for model in MODELS
        for prompt_index, prompt in enumerate(PROMPTS)
    ]
    return dict(await asyncio.gather(*tasks))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json()
    except JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must be valid JSON",
        ) from exc

    if benchmark_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SOC benchmark already running",
        )

    async with benchmark_lock:
        logger.info("accepted benchmark payload")
        results = await benchmark(payload)

    return {"status": "completed", "results": results}


if __name__ == "__main__":
    host = os.getenv("BENCHMARK_HOST", "0.0.0.0")
    port = int(os.getenv("BENCHMARK_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
