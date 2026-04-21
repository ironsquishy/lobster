# Lobster

Lobster is the OpenAI-compatible adapter between Open WebUI and OpenClaw.

## Features

- `/v1/models`
- `/v1/chat/completions`
- streaming passthrough
- verbose logging
- SQLite per-user memory
- safe memory injection
- rule-based durable memory extraction

## Environment

Copy `.env.example` to `.env` and fill in values.

## Run locally

```bash
docker build -t lobster .
docker run --rm -p 4000:4000 --env-file .env -v $(pwd)/data:/app/data lobster

---

# Docker compose note

In your Shrimpy stack, make sure Lobster has a persistent volume:

```yaml
lobster:
  build:
    context: ./lobster
  env_file:
    - .env
  expose:
    - "4000"
  volumes:
    - ./lobster/data:/app/data