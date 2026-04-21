from __future__ import annotations

import re

DURABLE_PATTERNS = [
    ("preference", re.compile(r"\bprefer\b.+", re.IGNORECASE)),
    ("project", re.compile(r"\bworking on\b.+", re.IGNORECASE)),
    ("project", re.compile(r"\bbuilding\b.+", re.IGNORECASE)),
    ("fact", re.compile(r"\bmy name is\b.+", re.IGNORECASE)),
    ("fact", re.compile(r"\bi use\b.+", re.IGNORECASE)),
]

SENSITIVE_HINTS = [
    "password",
    "token",
    "secret",
    "api key",
    "private key",
    "ssn",
    "social security",
    "diagnosis",
    "medical",
]


def should_skip_memory(text: str) -> bool:
    lower = text.lower()
    return any(hint in lower for hint in SENSITIVE_HINTS)


def extract_candidate_memories(user_text: str) -> list[tuple[str, str, list[str]]]:
    if should_skip_memory(user_text):
        return []

    out: list[tuple[str, str, list[str]]] = []
    for scope, pattern in DURABLE_PATTERNS:
        match = pattern.search(user_text)
        if match:
            content = match.group(0).strip()
            keywords = [w.lower() for w in re.findall(r"[A-Za-z0-9_-]{3,}", content)[:8]]
            out.append((scope, content, keywords))
    return out