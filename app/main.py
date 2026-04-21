from __future__ import annotations

import json
import logging
import os
import time
import traceback
import uuid
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.auth import require_bearer
from app.openclaw_client import chat_completions, list_models, stream_chat_completions
from app.schemas import ChatCompletionsRequest, ModelCard, ModelsResponse

LOG_LEVEL = os.getenv("LOBSTER_LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [lobster] %(message)s",
)
logger = logging.getLogger("lobster")

app = FastAPI(title="Lobster", version="0.6.0")


def _safe_json(data: Any, limit: int = 4000) -> str:
    try:
        text = json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        text = repr(data)
    if len(text) > limit:
        return text[:limit] + "\n...<truncated>..."
    return text


@app.get("/healthz")
async def healthz() -> dict[str, bool]:
    logger.info("healthz ok")
    return {"ok": True}


@app.get("/v1/models", dependencies=[Depends(require_bearer)])
async def get_models():
    req_id = str(uuid.uuid4())[:8]
    started = time.time()
    logger.info("[%s] GET /v1/models start", req_id)

    try:
        upstream = await list_models()
        logger.info(
            "[%s] GET /v1/models success in %.2fs body=%s",
            req_id,
            time.time() - started,
            _safe_json(upstream, 2000),
        )
        return JSONResponse(content=upstream)

    except Exception as exc:
        logger.error(
            "[%s] GET /v1/models failed in %.2fs error=%r\n%s",
            req_id,
            time.time() - started,
            exc,
            traceback.format_exc(),
        )
        raise HTTPException(status_code=502, detail=f"upstream_error: {exc}") from exc


@app.post("/v1/chat/completions", dependencies=[Depends(require_bearer)])
async def post_chat_completions(
    req: ChatCompletionsRequest,
    authorization: str | None = Header(default=None),
):
    req_id = str(uuid.uuid4())[:8]
    started = time.time()

    payload = req.model_dump(exclude_none=True)

    logger.info(
        "[%s] POST /v1/chat/completions start stream=%s model=%s",
        req_id,
        payload.get("stream", False),
        payload.get("model"),
    )
    logger.info("[%s] incoming payload=%s", req_id, _safe_json(payload))

    # Optional guardrails while debugging
    payload.setdefault("max_tokens", 128)
    payload.setdefault("temperature", 0)

    if payload.get("stream", False):
        logger.info("[%s] streaming mode enabled", req_id)

        async def event_stream():
            try:
                async for chunk in stream_chat_completions(payload):
                    logger.info("[%s] stream chunk bytes=%d", req_id, len(chunk))
                    yield chunk
                logger.info("[%s] stream complete in %.2fs", req_id, time.time() - started)
            except Exception as exc:
                logger.error(
                    "[%s] stream failed in %.2fs error=%r\n%s",
                    req_id,
                    time.time() - started,
                    exc,
                    traceback.format_exc(),
                )
                message = str(exc).replace("\n", " ")
                yield f"event: error\ndata: {message}\n\n".encode("utf-8")

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    try:
        upstream = await chat_completions(payload)

        logger.info(
            "[%s] upstream success in %.2fs body=%s",
            req_id,
            time.time() - started,
            _safe_json(upstream, 3000),
        )
        return JSONResponse(content=upstream)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "[%s] upstream failed in %.2fs error=%r\n%s",
            req_id,
            time.time() - started,
            exc,
            traceback.format_exc(),
        )
        raise HTTPException(status_code=502, detail=f"upstream_error: {exc}") from exc
