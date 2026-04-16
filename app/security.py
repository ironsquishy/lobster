import os
from fastapi import HTTPException

SECRET = os.getenv("PUBLIC_SHARED_SECRET", "")


def verify_secret(header_value: str | None) -> None:
    if not SECRET:
        raise HTTPException(status_code=500, detail="server_secret_not_configured")
    if header_value != SECRET:
        raise HTTPException(status_code=401, detail="unauthorized")