import asyncio
import json
import logging
import os
from json import JSONDecodeError
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status

from agent import SOCAgent


DEFAULT_FLAG = "flag{stochastic_parrot}"
PENDING_MESSAGE = "Halting request, pending soc investigation"
REVOKED_MESSAGE = "Attack detected; access has been revoked"

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8000"))
FLAG_HOST = os.getenv("FLAG_HOST", "0.0.0.0")
FLAG_PORT = int(os.getenv("FLAG_PORT", "8001"))
FLAG_VALUE = os.getenv("INITIAL_FLAG", DEFAULT_FLAG)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("agentic-soc")

webhook_app = FastAPI(title="Agentic SOC webhook")
flag_app = FastAPI(title="Agentic SOC flag")

agent = SOCAgent()
investigation_lock = asyncio.Lock()


async def investigate(payload: Any) -> None:
    await agent.reset_result()
    evidence = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    await agent.investigate(evidence)


@webhook_app.get("/health")
async def webhook_health() -> dict[str, str]:
    return {"status": "ok"}


@flag_app.get("/health")
async def flag_health() -> dict[str, str]:
    return {"status": "ok"}


@flag_app.get("/flag")
async def get_flag() -> dict[str, str]:
    if investigation_lock.locked():
        return {"status": PENDING_MESSAGE}

    if agent.is_revoked:
        return {"flag": REVOKED_MESSAGE, "report": agent.report}

    return {"flag": FLAG_VALUE, "report": agent.report}


@webhook_app.post("/webhook")
async def webhook(request: Request) -> dict[str, str]:
    try:
        payload = await request.json()
    except JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must be valid JSON",
        ) from exc

    if investigation_lock.locked():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SOC investigation already running",
        )

    async with investigation_lock:
        logger.info("accepted webhook payload")
        await investigate(payload)

    return {"status": "completed"}


async def serve() -> None:
    webhook_config = uvicorn.Config(
        webhook_app,
        host=WEBHOOK_HOST,
        port=WEBHOOK_PORT,
    )
    flag_config = uvicorn.Config(
        flag_app,
        host=FLAG_HOST,
        port=FLAG_PORT,
    )

    logger.info("starting webhook server on %s:%s", WEBHOOK_HOST, WEBHOOK_PORT)
    logger.info("starting flag server on %s:%s", FLAG_HOST, FLAG_PORT)

    await asyncio.gather(
        uvicorn.Server(webhook_config).serve(),
        uvicorn.Server(flag_config).serve(),
    )


if __name__ == "__main__":
    asyncio.run(serve())
