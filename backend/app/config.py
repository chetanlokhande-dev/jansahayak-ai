"""Application settings, loaded from environment variables (never from frontend code)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

try:  # python-dotenv is optional at import time
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "data"

if load_dotenv:
    load_dotenv(BASE_DIR / ".env")

# Languages the MVP supports. `gemini_name` is used inside prompts.
LANGUAGES = {
    "en": {"label": "English", "native": "English", "gemini_name": "English", "speech": "en-IN"},
    "hi": {"label": "Hindi", "native": "हिन्दी", "gemini_name": "Hindi (Devanagari script)", "speech": "hi-IN"},
    "mr": {"label": "Marathi", "native": "मराठी", "gemini_name": "Marathi (Devanagari script)", "speech": "mr-IN"},
}
DEFAULT_LANGUAGE = "en"

OFFICIAL_PORTALS = [
    {"title": "myScheme - Government scheme discovery", "url": "https://www.myscheme.gov.in/"},
    {"title": "National Portal of India", "url": "https://www.india.gov.in/"},
    {"title": "Legislative Department", "url": "https://legislative.gov.in/"},
    {"title": "Press Information Bureau", "url": "https://www.pib.gov.in/"},
    {"title": "National Legal Services Authority", "url": "https://www.nalsa.gov.in/"},
]


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_s: float = 60.0
    allowed_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    max_upload_mb: int = 10
    max_text_chars: int = 200_000
    db_path: Path = field(default_factory=lambda: BASE_DIR / "jansahayak.db")
    ocr_langs: str = "eng+hin+mar"
    rate_limit_per_minute: int = 30

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key.strip())


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(v.strip() for v in value.split(",") if v.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    origins = os.getenv("ALLOWED_ORIGINS", "")
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        allowed_origins=_split_csv(origins) or Settings.allowed_origins,
        max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "10")),
        db_path=Path(os.getenv("DB_PATH", str(BASE_DIR / "jansahayak.db"))),
        ocr_langs=os.getenv("OCR_LANGS", "eng+hin+mar"),
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "30")),
    )
