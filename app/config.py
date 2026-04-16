from __future__ import annotations

import os

LOBSTER_API_KEY = os.getenv("LOBSTER_API_KEY", "change-me")
OPENCLAW_BASE_URL = os.getenv("OPENCLAW_BASE_URL", "http://goliath.tail14f50f.ts.net:18789/v1").rstrip("/")
OPENCLAW_BEARER_TOKEN = os.getenv("OPENCLAW_BEARER_TOKEN", "")
DEFAULT_MODEL_ID = os.getenv("DEFAULT_MODEL_ID", "openclaw/default")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "300"))