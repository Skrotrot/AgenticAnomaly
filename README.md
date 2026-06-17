# AgenticAnomaly - Indirect Prompt Injection CTF for Agentic SOCs

AgenticAnomaly is an **indirect prompt injection CTF** for testing how **agentic security operations center (SOC)** workflows can be exploited through malicious input. The project demonstrates how modern SOC solutions that rely on **large language models (LLMs)** for detection and response can be vulnerable to prompt injection attacks.

The lab was developed as part of the **EP284U** course at the **KTH Royal Institute of Technology**.

## Agentic SOC CTF Setup

To get started and try out the CTF, start by cloning the repo.


```bash
git clone https://github.com/skrotrot/agenticanomaly.git

cd agenticanomaly
```

The demo agentic SOC requires an OpenRouter API key with credits. Place your API key in a `.env` file in the same directory as `docker-compose.yml`, formatted as follows:

```env
OPENROUTER_API_KEY=CHANGE-THIS-TO-YOUR-API-KEY
```

You need Docker installed on your computer. After that, the CTF can be started using Docker Compose.

```bash
docker compose up -d
```

The CTF will be available on localhost after the containers start. The mTLS website is exposed on port `8443`, and the jump server is exposed on port `22`.


## Prompt Injection Exploit Example

A full exploit example is available in `pwn-script.sh`. This script uses the prompt injection from `prompt-injection`, base64-encoded in the following command:

```bash
sudo echo BASE64STRING=
```

## Prompt Injection Benchmarks

Due to the probabilistic nature of LLMs, exploits that work once may fail the next time. In `benchmark/benchmark.md`, you will find benchmarks of the example prompt as well as false positives and false negatives by the agent.
