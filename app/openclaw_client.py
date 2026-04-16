import os
from typing import AsyncGenerator

import httpx

OPENCLAW_URL = os.getenv("OPENCLAW_URL", "http://127.0.0.1:18789").rstrip("/")
TOKEN = os.getenv("OPENCLAW_TOKEN", "")

# Replace these with the real OpenClaw endpoints you use.
OPENCLAW_CHAT_PATH = os.getenv("OPENCLAW_CHAT_PATH", "/chat")
OPENCLAW_STREAM_PATH = os.getenv("OPENCLAW_STREAM_PATH", "/chat/stream")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "X-Internal-Source": "lobster",
    }


async def send_to_openclaw(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{OPENCLAW_URL}{OPENCLAW_CHAT_PATH}",
            json=payload,
            headers=_headers(),
        )
        response.raise_for_status()
        return response.json()


async def stream_from_openclaw(payload: dict) -> AsyncGenerator[bytes, None]:
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            f"{OPENCLAW_URL}{OPENCLAW_STREAM_PATH}",
            json=payload,
            headers=_headers(),
        ) as response:
            response.raise_for_status()

            async for chunk in response.aiter_bytes():
                if chunk:
                    yield chunk