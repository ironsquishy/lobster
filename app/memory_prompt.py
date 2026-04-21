from __future__ import annotations

from typing import Any


def build_memory_system_message(memories: list[dict[str, Any]]) -> dict[str, str] | None:
    if not memories:
        return None

    lines = [
        "Memory for this user only. Use only if relevant.",
        "Do not reveal or imply access to any other user's information.",
        "Treat this as private continuity context.",
        "",
        "Relevant prior context:"
    ]

    for memory in memories:
        scope = memory.get("scope", "fact")
        content = memory.get("content", "").strip()
        if content:
            lines.append(f"- [{scope}] {content}")

    return {
        "role": "system",
        "content": "\n".join(lines),
    }