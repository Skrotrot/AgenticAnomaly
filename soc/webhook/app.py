import asyncio
import json
import logging
import os
import urllib.request
from json import JSONDecodeError
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status


AGENT_COMMAND = ("opencode", "run", "--agent", "soc")
DEFAULT_TIMEOUT_SECONDS = 300
CONTROL_URL = os.getenv("MTLS_WEBSITE_CONTROL_URL", "http://mtls-website:8444")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("vector-opencode-webhook")

app = FastAPI(title="Vector to OpenCode SOC Webhook")
investigation_lock = asyncio.Lock()


def opencode_timeout_seconds() -> float:
    raw_value = os.getenv("OPENCODE_TIMEOUT_SECONDS")
    if raw_value is None:
        return DEFAULT_TIMEOUT_SECONDS

    try:
        timeout = float(raw_value)
    except ValueError as exc:
        raise RuntimeError("OPENCODE_TIMEOUT_SECONDS must be a number") from exc

    if timeout <= 0:
        raise RuntimeError("OPENCODE_TIMEOUT_SECONDS must be greater than 0")

    return timeout


async def control(action: str) -> None:
    url = f"{CONTROL_URL}/{action}"
    request = urllib.request.Request(url, data=b"", method="POST")

    def post() -> None:
        with urllib.request.urlopen(request, timeout=10):
            pass

    await asyncio.to_thread(post)


async def run_opencode_agent(payload: Any) -> None:
    payload_arg = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    command = (*AGENT_COMMAND, payload_arg)
    timeout = opencode_timeout_seconds()

    logger.info("starting opencode agent command=%s timeout=%s", AGENT_COMMAND, timeout)

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        logger.exception("opencode executable was not found")
        return

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        stdout, stderr = await process.communicate()
        logger.error(
            "opencode agent timed out after %s seconds stdout=%r stderr=%r",
            timeout,
            stdout.decode(errors="replace")[:2000],
            stderr.decode(errors="replace")[:2000],
        )
        return

    logger.info(
        "opencode agent finished returncode=%s stdout=%r stderr=%r",
        process.returncode,
        stdout.decode(errors="replace"),
        stderr.decode(errors="replace"),
    )
    if process.returncode != 0:
        raise RuntimeError(f"opencode agent failed with return code {process.returncode}")


async def investigate(payload: Any) -> None:
    try:
        await control("pause")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to pause mTLS website",
        ) from exc

    try:
        await run_opencode_agent(payload)
    finally:
        try:
            await control("resume")
        except Exception:
            logger.exception("failed to resume mTLS website")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook")
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
        logger.info("accepted vector webhook payload")
        await investigate(payload)

    return {"status": "completed"}


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app:app", host=host, port=port)
