from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.auth import require_bearer
from app.config import DEFAULT_MODEL_ID
from app.openclaw_client import chat_completions, list_models, stream_chat_completions
from app.schemas import ChatCompletionsRequest, ModelCard, ModelsResponse

app = FastAPI(title="Lobster", version="0.3.0")


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}


@app.get("/v1/models", dependencies=[Depends(require_bearer)])
async def get_models():
    try:
        upstream = await list_models()
        return JSONResponse(content=upstream)
    except Exception:
        fallback = ModelsResponse(data=[ModelCard(id=DEFAULT_MODEL_ID)])
        return JSONResponse(content=fallback.model_dump())


@app.post("/v1/chat/completions", dependencies=[Depends(require_bearer)])
async def post_chat_completions(req: ChatCompletionsRequest):
    payload = req.model_dump(exclude_none=True)

    try:
        if req.stream:
            async def event_stream():
                try:
                    async for chunk in stream_chat_completions(payload):
                        yield chunk
                except Exception as exc:
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

        upstream = await chat_completions(payload)
        return JSONResponse(content=upstream)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"upstream_error: {exc}") from exc