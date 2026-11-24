"""Thin Gemini REST client. The API key is read from the environment on the server only."""
from __future__ import annotations

import json
import re
from typing import Any

from ..config import Settings

API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiError(RuntimeError):
    """Raised when the Gemini API is unreachable or returns an error (message is safe to show)."""


class GeminiClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return self.settings.gemini_enabled

    async def generate(
        self,
        system: str,
        contents: list[dict[str, Any]],
        json_mode: bool = False,
        temperature: float = 0.2,
        max_output_tokens: int = 2048,
    ) -> str:
        if not self.enabled:
            raise GeminiError("Gemini API key is not configured.")
        try:
            import httpx
        except ImportError as e:  # pragma: no cover
            raise GeminiError("The 'httpx' package is not installed on the server.") from e

        body: dict[str, Any] = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_output_tokens},
        }
        if json_mode:
            body["generationConfig"]["responseMimeType"] = "application/json"

        url = f"{API_ROOT}/{self.settings.gemini_model}:generateContent"
        headers = {"x-goog-api-key": self.settings.gemini_api_key, "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.settings.gemini_timeout_s) as client:
                resp = await client.post(url, headers=headers, json=body)
        except httpx.HTTPError as e:
            raise GeminiError("Could not reach the Gemini service. Please try again.") from e

        if resp.status_code == 429:
            raise GeminiError("The AI service is busy right now. Please try again in a minute.")
        if resp.status_code in (400, 401, 403):
            raise GeminiError("The AI service rejected the request. Check the server's Gemini API key and model name.")
        if resp.status_code >= 400:
            raise GeminiError("The AI service returned an error. Please try again.")

        try:
            data = resp.json()
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts).strip()
        except (KeyError, IndexError, ValueError) as e:
            raise GeminiError("The AI service returned an empty or blocked response. Try rephrasing.") from e


def user_turn(text: str) -> dict[str, Any]:
    return {"role": "user", "parts": [{"text": text}]}


def model_turn(text: str) -> dict[str, Any]:
    return {"role": "model", "parts": [{"text": text}]}


def parse_json(text: str) -> dict[str, Any] | None:
    """Parse a JSON object from model output, tolerating code fences. Returns None on failure."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else None
    except ValueError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                value = json.loads(match.group(0))
                return value if isinstance(value, dict) else None
            except ValueError:
                return None
    return None
