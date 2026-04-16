from __future__ import annotations

import httpx

from app.config import OPENCLAW_BASE_URL, OPENCLAW_BEARER_TOKEN, REQUEST_TIMEOUT_SECONDS


def _headers() -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
    }
    if OPENCLAW_BEARER_TOKEN:
        headers["Authorization"] = f"Bearer {OPENCLAW_BEARER_TOKEN}"
    return headers


async def list_models() -> dict:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.get(f"{OPENCLAW_BASE_URL}/models", headers=_headers())
        response.raise_for_status()
        return response.json()


async def chat_completions(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.post(
            f"{OPENCLAW_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
        )
        response.raise_for_status()
        return response.json()


async def stream_chat_completions(payload: dict):
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            f"{OPENCLAW_BASE_URL}/chat/completions",
            headers={**_headers(), "Accept": "text/event-stream"},
            json=payload,
        ) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                if chunk:
                    yield chunk