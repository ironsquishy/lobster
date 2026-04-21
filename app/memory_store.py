from __future__ import annotations

import json
import sqlite3
import time
from typing import Any

from app.config import MEMORY_DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(MEMORY_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            scope TEXT NOT NULL,
            content TEXT NOT NULL,
            keywords TEXT NOT NULL DEFAULT '[]',
            source_session_id TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            last_used_at INTEGER NOT NULL
        )
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_memories_user_id
        ON memories(user_id)
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_memories_user_scope
        ON memories(user_id, scope)
        """)


def add_memory(
    user_id: str,
    content: str,
    scope: str = "fact",
    keywords: list[str] | None = None,
    source_session_id: str | None = None,
) -> None:
    now = int(time.time())
    keywords = keywords or []

    with get_conn() as conn:
        conn.execute("""
        INSERT INTO memories (
            user_id, scope, content, keywords, source_session_id,
            created_at, updated_at, last_used_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            scope,
            content.strip(),
            json.dumps(keywords),
            source_session_id,
            now,
            now,
            now,
        ))


def search_memories(user_id: str, query: str, limit: int = 6) -> list[dict[str, Any]]:
    tokens = [t.lower() for t in query.split() if len(t) > 2]

    with get_conn() as conn:
        rows = conn.execute("""
        SELECT * FROM memories
        WHERE user_id = ?
        ORDER BY last_used_at DESC, updated_at DESC
        LIMIT 50
        """, (user_id,)).fetchall()

    scored: list[tuple[int, sqlite3.Row]] = []
    for row in rows:
        score = 0
        haystack = f"{row['content']} {row['keywords']}".lower()
        for token in tokens:
            if token in haystack:
                score += 1
        if score > 0:
            scored.append((score, row))

    scored.sort(key=lambda x: (-x[0], -x[1]["updated_at"]))
    top_rows = [row for _, row in scored[:limit]]

    if not top_rows:
        top_rows = rows[:limit]

    out: list[dict[str, Any]] = []
    now = int(time.time())
    with get_conn() as conn:
        for row in top_rows:
            conn.execute(
                "UPDATE memories SET last_used_at = ? WHERE id = ?",
                (now, row["id"]),
            )
            out.append(dict(row))
    return out