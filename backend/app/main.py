"""JanSahayak AI - FastAPI backend.

Run locally:  uvicorn app.main:app --reload --port 8000   (from the backend/ folder)
"""
from __future__ import annotations

import re
import time
from collections import defaultdict, deque
from functools import lru_cache
from typing import Any

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from .config import DATA_DIR, DEFAULT_LANGUAGE, LANGUAGES, OFFICIAL_PORTALS, Settings, get_settings
from .schemas import ChatRequest, EligibilityRequest, TranslateRequest
from .services import assistant, documents, eligibility, knowledge
from .services.gemini import GeminiError
from .services.store import Store

APP_NAME = "JanSahayak AI"
TAGLINE = "Government Information. Simplified for Everyone."

app = FastAPI(title=APP_NAME, description=TAGLINE, version="0.1.0")

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


# ---------- dependencies ----------

@lru_cache(maxsize=1)
def get_store() -> Store:
    return Store(get_settings().db_path)


_CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9-]{16,64}$")
_hits: dict[str, deque[float]] = defaultdict(deque)


def client_id(x_client_id: str = Header(default="")) -> str:
    if not _CLIENT_ID_RE.match(x_client_id):
        raise HTTPException(400, "Missing or invalid X-Client-Id header.")
    return x_client_id


def rate_limited(cid: str = Depends(client_id)) -> str:
    limit = get_settings().rate_limit_per_minute
    now = time.monotonic()
    window = _hits[cid]
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= limit:
        raise HTTPException(429, "Too many requests. Please wait a minute and try again.")
    window.append(now)
    return cid


def valid_language(code: str) -> str:
    if code not in LANGUAGES:
        raise HTTPException(400, f"Unsupported language. Choose one of: {', '.join(LANGUAGES)}.")
    return code


# ---------- meta ----------

@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "app": APP_NAME}


@app.get("/api/meta")
def meta() -> dict[str, Any]:
    s: Settings = get_settings()
    return {
        "app": APP_NAME,
        "tagline": TAGLINE,
        "languages": [{"code": c, **{k: v for k, v in info.items() if k != "gemini_name"}} for c, info in LANGUAGES.items()],
        "default_language": DEFAULT_LANGUAGE,
        "ai_mode": "gemini" if s.gemini_enabled else "offline",
        "max_upload_mb": s.max_upload_mb,
        "official_portals": OFFICIAL_PORTALS,
        "knowledge_base": knowledge.kb_meta(),
    }


# ---------- schemes & rights ----------

@app.get("/api/schemes")
def schemes(q: str = Query(default="", max_length=100), category: str = Query(default="", max_length=40)) -> dict[str, Any]:
    items = knowledge.list_schemes()
    if category:
        items = [s for s in items if s["category"] == category]
    if q.strip():
        needle = q.strip().lower()
        items = [s for s in items if needle in " ".join([s["name"], s["summary"], " ".join(s.get("keywords", []))]).lower()]
    return {"schemes": items, "categories": knowledge.categories(), "data_status": knowledge.kb_meta()["schemes"]}


@app.get("/api/schemes/{scheme_id}")
def scheme_detail(scheme_id: str) -> dict[str, Any]:
    scheme = knowledge.get_scheme(scheme_id)
    if not scheme:
        raise HTTPException(404, "Scheme not found.")
    return scheme


@app.get("/api/rights")
def rights() -> dict[str, Any]:
    return {"rights": knowledge.list_rights(), "data_status": knowledge.kb_meta()["rights"]}


@app.get("/api/rights/{right_id}")
def right_detail(right_id: str) -> dict[str, Any]:
    right = knowledge.get_right(right_id)
    if not right:
        raise HTTPException(404, "Right not found.")
    return right


# ---------- chat ----------

@app.post("/api/chat")
async def chat(req: ChatRequest, cid: str = Depends(rate_limited), store: Store = Depends(get_store)) -> dict[str, Any]:
    language = valid_language(req.language)
    message = req.message.strip()
    if not message:
        raise HTTPException(400, "Please type a question.")

    history: list[dict[str, Any]] = []
    doc_id = req.document_id
    if req.conversation_id:
        conv = store.get_conversation(cid, req.conversation_id)
        if not conv:
            raise HTTPException(404, "Conversation not found.")
        conv_id = conv["id"]
        doc_id = doc_id or conv["document_id"]
        history = store.messages(conv_id)
    else:
        conv_id = None

    doc = None
    if doc_id:
        doc = store.get_document(cid, doc_id)
        if not doc:
            raise HTTPException(404, "Document not found.")

    result = await assistant.answer(message, language, history, doc, get_settings())

    if conv_id is None:
        conv_id = store.create_conversation(cid, message, language, doc_id)
    store.add_message(conv_id, "user", message)
    extra = {k: result[k] for k in ("verified", "inferred", "unavailable", "follow_ups", "sources", "mode", "notice")}
    message_id = store.add_message(conv_id, "assistant", result["answer"], extra)
    return {"conversation_id": conv_id, "message_id": message_id, "answer": result["answer"], **extra}


# ---------- documents ----------

async def _process_document(filename: str, data: bytes, language: str, cid: str, store: Store) -> dict[str, Any]:
    settings = get_settings()
    name = documents.safe_filename(filename)
    try:
        extracted = await run_in_threadpool(documents.extract_text, name, data, settings.ocr_langs, settings.max_text_chars)
    except documents.DocumentError as e:
        raise HTTPException(422, str(e)) from e

    outcome = await assistant.analyze_document(extracted.text, name, language, settings)
    doc_id = store.add_document(cid, name, extracted.kind, extracted.method, extracted.text,
                                outcome["analysis"], language, extracted.warnings)
    return {
        "document": {"id": doc_id, "filename": name, "kind": extracted.kind, "method": extracted.method,
                     "pages": extracted.pages, "chars": len(extracted.text), "language": language,
                     "warnings": extracted.warnings},
        "analysis": outcome["analysis"], "mode": outcome["mode"], "notice": outcome["notice"],
    }


@app.post("/api/documents")
async def upload_document(
    file: UploadFile = File(...), language: str = Form(DEFAULT_LANGUAGE),
    cid: str = Depends(rate_limited), store: Store = Depends(get_store),
) -> dict[str, Any]:
    language = valid_language(language)
    limit = get_settings().max_upload_bytes
    data = await file.read(limit + 1)  # never read more than the limit into memory
    if len(data) > limit:
        raise HTTPException(413, f"File is too large. The limit is {get_settings().max_upload_mb} MB.")
    return await _process_document(file.filename or "document", data, language, cid, store)


@app.get("/api/sample-documents")
def sample_documents() -> dict[str, Any]:
    folder = DATA_DIR / "sample_documents"
    return {"documents": sorted(p.name for p in folder.glob("*.txt")), "note": "Fictional sample documents for testing."}


@app.post("/api/sample-documents/{name}")
async def analyze_sample(
    name: str, language: str = Query(DEFAULT_LANGUAGE), cid: str = Depends(rate_limited), store: Store = Depends(get_store)
) -> dict[str, Any]:
    language = valid_language(language)
    path = DATA_DIR / "sample_documents" / name
    if name not in {p.name for p in (DATA_DIR / "sample_documents").glob("*.txt")}:
        raise HTTPException(404, "Sample document not found.")
    return await _process_document(name, path.read_bytes(), language, cid, store)


@app.get("/api/documents")
def list_documents(cid: str = Depends(client_id), store: Store = Depends(get_store)) -> dict[str, Any]:
    return {"documents": store.list_documents(cid)}


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str, cid: str = Depends(client_id), store: Store = Depends(get_store)) -> dict[str, Any]:
    doc = store.get_document(cid, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found.")
    return {"document": {k: doc[k] for k in ("id", "filename", "kind", "method", "language", "created_at", "warnings")},
            "analysis": doc["analysis"], "text_preview": doc["text"][:1500]}


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str, cid: str = Depends(client_id), store: Store = Depends(get_store)) -> dict[str, bool]:
    if not store.delete_document(cid, doc_id):
        raise HTTPException(404, "Document not found.")
    return {"deleted": True}


# ---------- eligibility ----------

@app.get("/api/eligibility/fields")
def eligibility_fields(lang: str = Query(DEFAULT_LANGUAGE)) -> dict[str, Any]:
    return {"fields": eligibility.fields_for_language(valid_language(lang))}


@app.post("/api/eligibility/check")
async def eligibility_check(req: EligibilityRequest, cid: str = Depends(rate_limited)) -> dict[str, Any]:
    language = valid_language(req.language)
    try:
        result = eligibility.check_all(req.profile)
    except eligibility.ProfileError as e:
        raise HTTPException(422, str(e)) from e
    explanation = await assistant.explain_eligibility(result, language, get_settings()) if req.explain else None
    return {**result, "explanation": explanation, "mode": "gemini" if explanation else "offline"}


# ---------- translate ----------

@app.post("/api/translate")
async def translate(req: TranslateRequest, cid: str = Depends(rate_limited)) -> dict[str, str]:
    target = valid_language(req.target_language)
    try:
        return {"translation": await assistant.translate(req.text, target, get_settings())}
    except GeminiError as e:
        raise HTTPException(503, str(e)) from e


# ---------- history ----------

@app.get("/api/history")
def history(cid: str = Depends(client_id), store: Store = Depends(get_store)) -> dict[str, Any]:
    return {"conversations": store.list_conversations(cid), "documents": store.list_documents(cid)}


@app.get("/api/history/conversations/{conv_id}")
def conversation(conv_id: str, cid: str = Depends(client_id), store: Store = Depends(get_store)) -> dict[str, Any]:
    conv = store.get_conversation(cid, conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found.")
    return {"conversation": conv, "messages": store.messages(conv_id)}


@app.delete("/api/history/conversations/{conv_id}")
def delete_conversation(conv_id: str, cid: str = Depends(client_id), store: Store = Depends(get_store)) -> dict[str, bool]:
    if not store.delete_conversation(cid, conv_id):
        raise HTTPException(404, "Conversation not found.")
    return {"deleted": True}


@app.delete("/api/history")
def clear_history(cid: str = Depends(client_id), store: Store = Depends(get_store)) -> dict[str, bool]:
    store.delete_all(cid)
    return {"deleted": True}


from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ---------- root & SPA ----------

@app.get("/")
def root():
    if FRONTEND_DIST.exists():
        return FileResponse(FRONTEND_DIST / "index.html")
    return {
        "status": "ok",
        "app": APP_NAME,
        "tagline": TAGLINE,
        "docs": "/docs",
        "health": "/api/health"
    }


FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.api_route("/api/{unmatched:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
    async def catch_all_api(unmatched: str):
        raise HTTPException(404, "API endpoint not found.")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")

