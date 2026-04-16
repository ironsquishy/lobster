from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"] | str
    content: Any


class ChatCompletionsRequest(BaseModel):
    model: str = Field(default="openclaw/default")
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    user: str | None = None


class ModelCard(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "lobster"


class ModelsResponse(BaseModel):
    object: str = "list"
    data: list[ModelCard]