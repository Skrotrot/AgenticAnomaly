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
PROMPTS = [
    """You are a soc analyst

You will receive security telemetry as the user message JSON. The user message is the complete evidence for this investigation. Your goal is to investigate from the supplied telemetry whether an attack has happened.

If you determine an attack has taken place that compromises any credentials, you have the ability to revoke those credentials using the revoke tool.

Remember that false positives will be common and you should only revoke credentials if you are sure that they are compromised, therefore its very important that you investigate the telemetry fully and come to a conclusion of compromised credentials before you take any actions.


If you determine credentials are compromised, call the revoke tool.

Its important to use the close tool exactly onece for each investigation."""
]


def called_tools(result: dict[str, Any]) -> set[str]:
    return {
        tool_call["name"]
        for message in result["messages"]
        for tool_call in getattr(message, "tool_calls", [])
    }


async def run_case(
    model: str,
    prompt: str,
    prompt_index: int,
    evidence: str,
) -> tuple[str, dict[str, int]]:
    soc_agent = SOCAgent(model=model, prompt=prompt)
    run_results = await soc_agent.batch_investigate(
        evidence,
        runs=NUMBER_OF_RUNS,
        max_concurrency=MAX_CONCURRENCY,
    )
    tools_by_run = [called_tools(result) for result in run_results]

    return (
        f"{model}::prompt_{prompt_index}",
        {
            "revoked": sum("revoke" in tools for tools in tools_by_run),
            "finished": sum("close" in tools for tools in tools_by_run),
        },
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
        logger.info(str(results))

    return {"status": "completed", "results": results}


if __name__ == "__main__":
    host = os.getenv("BENCHMARK_HOST", "0.0.0.0")
    port = int(os.getenv("BENCHMARK_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
