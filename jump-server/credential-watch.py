#!/usr/bin/env python3
import datetime
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


WATCH_FILE = Path(os.getenv("WATCH_FILE", "/root/client.key"))
SUDO_LOG = Path(os.getenv("SUDO_LOG", "/var/log/sudo.log"))
WEBHOOK_URL = os.getenv("SOC_WEBHOOK_URL", "http://soc:8000/webhook")
HTTP_TIMEOUT_SECONDS = float(os.getenv("SOC_WEBHOOK_TIMEOUT_SECONDS", "360"))
RETRY_DELAY_SECONDS = float(os.getenv("SOC_WEBHOOK_RETRY_DELAY_SECONDS", "5"))


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def read_text(path: Path) -> str:
    try:
        return path.read_text()
    except OSError as exc:
        print(f"failed to read {path}: {exc}", file=sys.stderr, flush=True)
        return ""


def wait_for_access() -> str:
    result = subprocess.run(
        [
            "inotifywait",
            "-q",
            "-e",
            "access",
            "--format",
            "%w%f %e",
            str(WATCH_FILE),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def build_payload(inotify_message: str) -> dict[str, object]:
    return {
        "kind": "credential_access_investigation",
        "timestamp": utc_now(),
        "host": socket.gethostname(),
        "inotify": {
            "file": str(WATCH_FILE),
            "event": "ACCESS",
            "message": inotify_message,
        },
        "sudo_log": {
            "path": str(SUDO_LOG),
            "contents": read_text(SUDO_LOG),
        },
    }


def post_payload(payload: dict[str, object]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode()
    request = urllib.request.Request(
        WEBHOOK_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    while True:
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                response.read()
            print(
                f"posted credential access investigation timestamp={payload['timestamp']}",
                flush=True,
            )
            return
        except urllib.error.HTTPError as exc:
            print(
                f"webhook returned HTTP {exc.code}; retrying in {RETRY_DELAY_SECONDS}s",
                file=sys.stderr,
                flush=True,
            )
        except Exception as exc:
            print(
                f"failed to post webhook: {exc}; retrying in {RETRY_DELAY_SECONDS}s",
                file=sys.stderr,
                flush=True,
            )
        time.sleep(RETRY_DELAY_SECONDS)


def main() -> None:
    print(f"watching {WATCH_FILE} for access events", flush=True)
    while True:
        inotify_message = wait_for_access()
        print(f"detected credential access: {inotify_message}", flush=True)
        post_payload(build_payload(inotify_message))


if __name__ == "__main__":
    main()
