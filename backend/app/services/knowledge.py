"""Loads the government knowledge base (sample data shipped with the repo).

Replace the JSON files in app/data with data ingested from verified official sources
before any real deployment. Nothing here invents data: it only reads the files.
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from ..config import DATA_DIR


def _load(name: str) -> dict[str, Any]:
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def schemes_data() -> dict[str, Any]:
    return _load("schemes.json")


@lru_cache(maxsize=1)
def rights_data() -> dict[str, Any]:
    return _load("rights.json")


def list_schemes() -> list[dict[str, Any]]:
    return schemes_data()["schemes"]


def list_rights() -> list[dict[str, Any]]:
    return rights_data()["rights"]


def get_scheme(scheme_id: str) -> dict[str, Any] | None:
    return next((s for s in list_schemes() if s["id"] == scheme_id), None)


def get_right(right_id: str) -> dict[str, Any] | None:
    return next((r for r in list_rights() if r["id"] == right_id), None)


def kb_meta() -> dict[str, Any]:
    return {
        "schemes": schemes_data()["_meta"],
        "rights": rights_data()["_meta"],
    }


def categories() -> list[str]:
    return sorted({s["category"] for s in list_schemes()})
