# Vector to OpenCode SOC Webhook

Small FastAPI webhook that accepts JSON from a Vector HTTP sink and runs:

```sh
opencode run --agent soc '<json-payload>'
```

The webhook pauses the mTLS website, runs OpenCode, then resumes the website.
Only one investigation runs at a time. If another webhook arrives while an
investigation is active, the service returns `503 Service Unavailable` so Vector
can retry.

## Install

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Run

```sh
python app.py
```

Optional runtime settings:

```sh
HOST=0.0.0.0 PORT=8000 OPENCODE_TIMEOUT_SECONDS=300 \
  MTLS_WEBSITE_CONTROL_URL=http://mtls-website:8444 python app.py
```

## Endpoints

- `GET /health`
- `POST /webhook`

Example:

```sh
curl -i \
  -H 'Content-Type: application/json' \
  -d '{"message":"example vector event","source_type":"demo"}' \
  http://localhost:8000/webhook
```
