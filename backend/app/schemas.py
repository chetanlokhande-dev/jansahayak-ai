"""Request models (input validation)."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en", max_length=5)
    conversation_id: Optional[str] = Field(default=None, max_length=64)
    document_id: Optional[str] = Field(default=None, max_length=64)


class EligibilityRequest(BaseModel):
    profile: dict[str, Any]
    language: str = Field(default="en", max_length=5)
    explain: bool = True


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    target_language: str = Field(max_length=5)
