import asyncio
import logging
import os
import ssl
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import PlainTextResponse


DEFAULT_FLAG = "flag{stochastic_parrot}"
PAUSED_MESSAGE = "Halting request, pending soc investigation"

SERVER_CERT_FILE = Path(os.getenv("SERVER_CERT_FILE", "/run/mtls/server.crt"))
SERVER_KEY_FILE = Path(os.getenv("SERVER_KEY_FILE", "/run/mtls/server.key"))
CLIENT_CA_FILE = Path(os.getenv("CLIENT_CA_FILE", "/run/mtls/client.crt"))

FLAG_HOST = os.getenv("FLAG_HOST", "0.0.0.0")
FLAG_PORT = int(os.getenv("FLAG_PORT", "8443"))
CONTROL_HOST = os.getenv("CONTROL_HOST", "0.0.0.0")
CONTROL_PORT = int(os.getenv("CONTROL_PORT", "8444"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("mtls-demo-website")

flag_app = FastAPI(title="mTLS Demo Flag")
control_app = FastAPI(title="mTLS Demo Controls")


class DemoState:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._flag = os.getenv("INITIAL_FLAG", DEFAULT_FLAG)
        self._report: str | None = None
        self._paused = False

    async def flag_response(self) -> str:
        async with self._lock:
            if self._paused:
                return PAUSED_MESSAGE
            if self._report is not None:
                return f"{self._flag}\n\n{self._report}"
            return self._flag

    async def replace_flag(self, flag: str) -> None:
        async with self._lock:
            self._flag = flag
            self._report = None

    async def publish_report(self, report: str) -> None:
        async with self._lock:
            self._report = report

    async def pause(self) -> None:
        async with self._lock:
            self._paused = True

    async def resume(self) -> None:
        async with self._lock:
            self._paused = False


state = DemoState()


def require_file(path: Path, description: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"{description} is required at {path}")


def validate_tls_files() -> None:
    require_file(SERVER_CERT_FILE, "server certificate")
    require_file(SERVER_KEY_FILE, "server private key")
    require_file(CLIENT_CA_FILE, "client CA certificate")


async def request_text(request: Request) -> str:
    body = await request.body()
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must be valid UTF-8",
        ) from exc


@flag_app.get("/flag", response_class=PlainTextResponse)
async def flag() -> str:
    return await state.flag_response()


@control_app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@control_app.post("/revoke")
async def revoke(request: Request) -> dict[str, str]:
    replacement = await request_text(request)
    await state.replace_flag(replacement)
    logger.info("flag response replaced via /revoke")
    return {"status": "updated"}


@control_app.post("/report")
async def report(request: Request) -> dict[str, str]:
    published_report = await request_text(request)
    await state.publish_report(published_report)
    logger.info("report published via /report")
    return {"status": "updated"}


@control_app.post("/pause")
async def pause() -> dict[str, str]:
    await state.pause()
    logger.info("flag endpoint paused")
    return {"status": "paused"}


@control_app.post("/resume")
async def resume() -> dict[str, str]:
    await state.resume()
    logger.info("flag endpoint resumed")
    return {"status": "resumed"}


async def serve() -> None:
    validate_tls_files()

    flag_config = uvicorn.Config(
        flag_app,
        host=FLAG_HOST,
        port=FLAG_PORT,
        ssl_certfile=str(SERVER_CERT_FILE),
        ssl_keyfile=str(SERVER_KEY_FILE),
        ssl_ca_certs=str(CLIENT_CA_FILE),
        ssl_cert_reqs=ssl.CERT_REQUIRED,
    )
    control_config = uvicorn.Config(
        control_app,
        host=CONTROL_HOST,
        port=CONTROL_PORT,
    )

    logger.info("starting mTLS flag server on %s:%s", FLAG_HOST, FLAG_PORT)
    logger.info("starting HTTP control server on %s:%s", CONTROL_HOST, CONTROL_PORT)

    await asyncio.gather(
        uvicorn.Server(flag_config).serve(),
        uvicorn.Server(control_config).serve(),
    )


if __name__ == "__main__":
    asyncio.run(serve())
