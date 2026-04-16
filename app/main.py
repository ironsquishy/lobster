from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.models import ChatRequest
from app.security import verify_secret
from app.openclaw_client import send_to_openclaw, stream_from_openclaw

app = FastAPI(title="Lobster", version="0.2.0")


@app.get("/healthz")
async def health():
    return {"ok": True}


@app.post("/v1/chat")
async def chat(req: ChatRequest, x_shrimpy_secret: str | None = Header(default=None)):
    verify_secret(x_shrimpy_secret)

    payload = req.to_internal()
    payload["stream"] = False

    try:
        result = await send_to_openclaw(payload)
        return JSONResponse(result)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"openclaw_error: {exc}") from exc


@app.post("/v1/chat/stream")
async def chat_stream(
    req: ChatRequest,
    x_shrimpy_secret: str | None = Header(default=None),
):
    verify_secret(x_shrimpy_secret)

    payload = req.to_internal()
    payload["stream"] = True

    async def event_stream():
        try:
            async for chunk in stream_from_openclaw(payload):
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