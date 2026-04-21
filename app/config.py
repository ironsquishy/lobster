from __future__ import annotations

import os
from pathlib import Path

LOBSTER_API_KEY = os.getenv("LOBSTER_API_KEY", "lobster_change_me")
OPENCLAW_BASE_URL = os.getenv("OPENCLAW_BASE_URL", "").rstrip("/")
OPENCLAW_BEARER_TOKEN = os.getenv("OPENCLAW_BEARER_TOKEN", "")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "300"))
LOBSTER_LOG_LEVEL = os.getenv("LOBSTER_LOG_LEVEL", "INFO").upper()
DEFAULT_MODEL_ID = os.getenv("DEFAULT_MODEL_ID", "openclaw/default")

# Use env override if present.
# Otherwise:
# - in Docker, /app exists, so use /app/data
# - locally, use repo-relative ./data
if "LOBSTER_DATA_DIR" in os.environ:
    DATA_DIR = Path(os.environ["LOBSTER_DATA_DIR"]).expanduser()
else:
    if Path("/app").exists():
        DATA_DIR = Path("/app/data")
    else:
        DATA_DIR = Path(__file__).resolve().parents[1] / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DB_PATH = DATA_DIR / "lobster_memory.sqlite3"