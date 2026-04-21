from __future__ import annotations

import json
import logging
import os

import httpx

OPENCLAW_BASE_URL = os.getenv("OPENCLAW_BASE_URL", "").rstrip("/")
OPENCLAW_BEARER_TOKEN = os.getenv("OPENCLAW_BEARER_TOKEN", "")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "300"))

logger = logging.getLogger("lobster")


def _headers() -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
    }
    if OPENCLAW_BEARER_TOKEN:
        headers["Authorization"] = f"Bearer {OPENCLAW_BEARER_TOKEN}"
    return headers


def _safe_text(text: str, limit: int = 3000) -> str:
    if len(text) > limit:
        return text[:limit] + "\n...<truncated>..."
    return text


def _redact(token: str) -> str:
    if not token:
        return "NONE"
    if len(token) <= 12:
        return "***REDACTED***"
    return f"{token[:6]}...{token[-6:]}"


async def list_models() -> dict:
    url = f"{OPENCLAW_BASE_URL}/models"

    logger.info("openclaw list_models url=%s", url)
    logger.info("openclaw token=%s", _redact(OPENCLAW_BEARER_TOKEN))

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.get(url, headers=_headers())
        logger.info(
            "openclaw list_models status=%s body=%s",
            response.status_code,
            _safe_text(response.text),
        )
        response.raise_for_status()
        return response.json()


async def chat_completions(payload: dict) -> dict:
    url = f"{OPENCLAW_BASE_URL}/chat/completions"

    logger.info("openclaw chat url=%s", url)
    logger.info("openclaw token=%s", _redact(OPENCLAW_BEARER_TOKEN))
    logger.info(
        "openclaw chat payload=%s",
        json.dumps(payload, indent=2, ensure_ascii=False),
    )

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.post(
            url,
            headers=_headers(),
            json=payload,
        )

        logger.info("openclaw chat status=%s", response.status_code)
        logger.info("openclaw chat headers=%s", dict(response.headers))
        logger.info("openclaw chat body=%s", _safe_text(response.text))

        response.raise_for_status()
        return response.json()


async def stream_chat_completions(payload: dict):
    url = f"{OPENCLAW_BASE_URL}/chat/completions"

    logger.info("openclaw stream url=%s", url)
    logger.info("openclaw token=%s", _redact(OPENCLAW_BEARER_TOKEN))
    logger.info(
        "openclaw stream payload=%s",
        json.dumps(payload, indent=2, ensure_ascii=False),
    )

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            url,
            headers={**_headers(), "Accept": "text/event-stream"},
            json=payload,
        ) as response:
            logger.info("openclaw stream status=%s", response.status_code)
            logger.info("openclaw stream headers=%s", dict(response.headers))
            response.raise_for_status()

            async for chunk in response.aiter_bytes():
                if chunk:
                    yield chunk
