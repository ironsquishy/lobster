from __future__ import annotations

import json
import logging
import time
import traceback
import uuid
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.auth import require_bearer
from app.config import DEFAULT_MODEL_ID, LOBSTER_LOG_LEVEL
from app.memory_prompt import build_memory_system_message
from app.memory_rules import extract_candidate_memories
from app.memory_store import add_memory, init_db, search_memories
from app.openclaw_client import chat_completions, list_models, stream_chat_completions
from app.schemas import ChatCompletionsRequest, ModelCard, ModelsResponse

logging.basicConfig(
    level=getattr(logging, LOBSTER_LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s [lobster] %(message)s",
)
logger = logging.getLogger("lobster")

app = FastAPI(title="Lobster", version="0.7.0")

init_db()


def _safe_json(data: Any, limit: int = 4000) -> str:
    try:
        text = json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        text = repr(data)
    if len(text) > limit:
        return text[:limit] + "\n...<truncated>..."
    return text


def _extract_last_user_text(messages: list[dict[str, Any]]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            return str(content)
    return ""


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
        fallback = ModelsResponse(data=[ModelCard(id=DEFAULT_MODEL_ID)])
        return JSONResponse(content=fallback.model_dump())


@app.post("/v1/chat/completions", dependencies=[Depends(require_bearer)])
async def post_chat_completions(
    req: ChatCompletionsRequest,
    authorization: str | None = Header(default=None),
):
    req_id = str(uuid.uuid4())[:8]
    started = time.time()
    payload = req.model_dump(exclude_none=True)

    logger.info(
        "[%s] POST /v1/chat/completions start stream=%s model=%s user=%s",
        req_id,
        payload.get("stream", False),
        payload.get("model"),
        payload.get("user"),
    )
    logger.info("[%s] incoming payload=%s", req_id, _safe_json(payload))

    payload.setdefault("max_tokens", 128)
    payload.setdefault("temperature", 0)

    user_id = payload.get("user")
    messages = payload.get("messages", [])

    if user_id:
        query_text = _extract_last_user_text(messages)
        memories = search_memories(user_id=user_id, query=query_text, limit=6)
        memory_msg = build_memory_system_message(memories)
        if memory_msg:
            payload["messages"] = [memory_msg] + messages
            logger.info("[%s] injected %d memories for user=%s", req_id, len(memories), user_id)
    else:
        logger.warning("[%s] no user id present; stateless mode only", req_id)

    logger.info("[%s] normalized payload=%s", req_id, _safe_json(payload))

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

        if user_id:
            last_user_text = _extract_last_user_text(messages)
            for scope, content, keywords in extract_candidate_memories(last_user_text):
                add_memory(
                    user_id=user_id,
                    content=content,
                    scope=scope,
                    keywords=keywords,
                    source_session_id=None,
                )
                logger.info("[%s] stored memory scope=%s user=%s content=%s", req_id, scope, user_id, content)

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