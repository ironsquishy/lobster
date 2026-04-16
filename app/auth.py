from __future__ import annotations

from fastapi import Header, HTTPException

from app.config import LOBSTER_API_KEY


def require_bearer(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    if token != LOBSTER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid bearer token")