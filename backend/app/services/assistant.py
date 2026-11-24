"""Orchestrates retrieval + Gemini (or an offline fallback) into grounded answers.

Every answer separates:
  verified     - stated directly in a retrieved source
  inferred     - a reasonable reading the sources do not state outright
  unavailable  - something the user asked about that the sources do not contain
"""
from __future__ import annotations

import re
from typing import Any

from ..config import LANGUAGES, OFFICIAL_PORTALS, Settings
from . import knowledge
from .gemini import GeminiClient, GeminiError, model_turn, parse_json, user_turn
from .retrieval import Hit, is_relevant, retrieve

SAMPLE_NOTE = "The knowledge base in this build is sample data. Please confirm details on the official source link."
OFFLINE_NOTICE = (
    "Gemini is not configured on this server, so this answer is taken directly from the built-in sample "
    "knowledge base (in English). Add GEMINI_API_KEY to enable translation and conversational answers."
)

BASE_RULES = """You are JanSahayak AI, a helper that explains Indian government schemes, policies, official notices and basic legal rights in simple language.
You are NOT an official government service and NOT a lawyer.

STRICT RULES
1. Use ONLY the information inside the numbered SOURCES. Never use outside knowledge for facts, amounts, dates, eligibility rules or legal provisions.
2. If the SOURCES do not contain the answer, say so plainly and list it under "unavailable". Do not guess.
3. Never invent eligibility criteria, benefits, deadlines or legal provisions.
4. Never guarantee that someone will qualify or be approved. Say they "may" qualify and should verify on the official source.
5. Do not give personal legal advice. For legal situations, explain the general right and suggest free legal aid (NALSA / District Legal Services Authority).
6. Use short sentences and everyday words. Explain any unavoidable technical term in brackets.
7. Write ALL text values in {language}. Keep scheme names, URLs and numbers unchanged.
8. If the data may be incomplete or sample data, say the user should confirm on the official source."""

CHAT_FORMAT = """Return ONLY a JSON object with these keys:
{{
  "answer": "the helpful answer in simple language. Short paragraphs or '- ' bullet lines. Mention source numbers like [S1] where used.",
  "verified": ["facts stated directly in the sources"],
  "inferred": ["reasonable conclusions the sources do not state outright (may be empty)"],
  "unavailable": ["things asked about that the sources do not contain (may be empty)"],
  "follow_ups": ["up to 3 short follow-up questions the user could ask next"],
  "source_ids": ["S1"]
}}"""


# ---------- helpers ----------

def _lang_name(code: str) -> str:
    return LANGUAGES.get(code, LANGUAGES["en"])["gemini_name"]


def _source_dict(sid: str, hit: Hit) -> dict[str, Any]:
    c = hit.chunk
    return {
        "id": sid, "title": c.title, "url": c.url, "section": c.section, "kind": c.kind,
        "data_status": c.meta.get("data_status", "user-document" if c.kind == "uploaded" else "sample"),
    }


def _fallback_sources() -> list[dict[str, Any]]:
    return [
        {"id": f"P{i}", "title": p["title"], "url": p["url"], "section": "", "kind": "portal", "data_status": "official-portal"}
        for i, p in enumerate(OFFICIAL_PORTALS, start=1)
    ]


def _build_context(hits: list[Hit]) -> tuple[str, list[dict[str, Any]]]:
    blocks, sources = [], []
    for i, hit in enumerate(hits, start=1):
        sid = f"S{i}"
        label = "UPLOADED DOCUMENT" if hit.chunk.kind == "uploaded" else "KNOWLEDGE BASE (sample data)"
        blocks.append(f"[{sid}] ({label}) {hit.chunk.title} - {hit.chunk.section}\n{hit.chunk.text}")
        sources.append(_source_dict(sid, hit))
    return "\n\n".join(blocks), sources


def _as_str_list(value: Any, limit: int = 8) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(v).strip() for v in value if str(v).strip()][:limit]


# ---------- offline rendering ----------

def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items)


def _render_scheme(s: dict[str, Any]) -> str:
    return (
        f"**{s['name']}**\n{s['summary']}\n\n"
        f"**Benefits**\n{_bullets(s['benefits'])}\n\n"
        f"**Who can apply**\n{_bullets(s['eligibility_text'])}\n\n"
        f"**Documents usually needed**\n{_bullets(s['required_documents'])}\n\n"
        f"**How to apply**\n{_bullets(s['how_to_apply'])}"
    )


def _render_right(r: dict[str, Any]) -> str:
    return (
        f"**{r['title']}**\n{r['summary']}\n\n**Key points**\n{_bullets(r['key_points'])}\n\n"
        f"**What you can do**\n{_bullets(r['what_to_do'])}\n\n_Law: {r['law']}_"
    )


def _offline_answer(hits: list[Hit], language: str) -> dict[str, Any]:
    top = hits[0].chunk
    unavailable = [] if language == "en" else ["Translation into your language needs the Gemini API key to be configured."]
    if top.kind == "scheme":
        body = _render_scheme(knowledge.get_scheme(top.ref_id))
    elif top.kind == "right":
        body = _render_right(knowledge.get_right(top.ref_id))
    else:
        quotes = [f"- {h.chunk.text.strip()[:400]}" for h in hits if h.chunk.kind == "uploaded"][:3]
        body = "Here are the parts of your document that are most relevant to your question:\n" + "\n".join(quotes)
    return {
        "answer": f"{body}\n\n{SAMPLE_NOTE}",
        "verified": [f"Taken directly from: {top.title}"],
        "inferred": [],
        "unavailable": unavailable,
        "follow_ups": [],
    }


def _no_answer(language: str) -> dict[str, Any]:
    return {
        "answer": (
            "I could not find this in my verified knowledge base, so I will not guess. "
            "Please check the official portals listed below, or try asking in a different way."
        ),
        "verified": [],
        "inferred": [],
        "unavailable": ["No matching verified source was found for this question."],
        "follow_ups": ["What schemes are available for farmers?", "What are my rights if I am arrested?"],
        "sources": _fallback_sources(),
    }


# ---------- public: chat ----------

async def _english_query(message: str, language: str, client: GeminiClient) -> str:
    """Translate a Hindi/Marathi question into English keywords so it matches the English KB."""
    if language == "en" or not client.enabled:
        return message
    try:
        text = await client.generate(
            "Translate the user's question into short English search keywords. Output only the English text.",
            [user_turn(message)], temperature=0.0, max_output_tokens=120,
        )
        return f"{message} {text}"
    except GeminiError:
        return message


async def answer(
    message: str, language: str, history: list[dict[str, str]], doc: dict[str, Any] | None, settings: Settings
) -> dict[str, Any]:
    client = GeminiClient(settings)
    query = await _english_query(message, language, client)
    hits = retrieve(query, doc)

    if not is_relevant(hits):
        out = _no_answer(language)
        out.update(mode="gemini" if client.enabled else "offline", notice=None if client.enabled else OFFLINE_NOTICE)
        return out

    context, sources = _build_context(hits)

    if not client.enabled:
        out = _offline_answer(hits, language)
        out.update(sources=sources[:3], mode="offline", notice=OFFLINE_NOTICE)
        return out

    system = BASE_RULES.format(language=_lang_name(language)) + "\n\n" + CHAT_FORMAT
    contents: list[dict[str, Any]] = []
    for m in history[-6:]:
        contents.append(user_turn(m["content"]) if m["role"] == "user" else model_turn(m["content"]))
    contents.append(user_turn(f"SOURCES:\n{context}\n\nUSER QUESTION:\n{message}"))

    try:
        raw = await client.generate(system, contents, json_mode=True)
    except GeminiError as e:
        out = _offline_answer(hits, language)
        out.update(sources=sources[:3], mode="offline", notice=f"{e} Showing the built-in knowledge base answer instead.")
        return out

    parsed = parse_json(raw)
    if not parsed or not str(parsed.get("answer", "")).strip():
        parsed = {"answer": raw, "verified": [], "inferred": [], "unavailable": [], "follow_ups": []}

    used = set(_as_str_list(parsed.get("source_ids"), 12))
    used_sources = [s for s in sources if s["id"] in used] or sources[:3]
    return {
        "answer": str(parsed["answer"]).strip(),
        "verified": _as_str_list(parsed.get("verified")),
        "inferred": _as_str_list(parsed.get("inferred")),
        "unavailable": _as_str_list(parsed.get("unavailable")),
        "follow_ups": _as_str_list(parsed.get("follow_ups"), 3),
        "sources": used_sources,
        "mode": "gemini",
        "notice": None,
    }


# ---------- public: document analysis ----------

DOC_FORMAT = """Return ONLY a JSON object with these keys (each a list of short strings except summary):
{{
  "summary": "2-4 simple sentences: what this document is and what it asks of the reader",
  "key_points": ["the most important points"],
  "benefits": ["benefits, amounts or entitlements mentioned (empty if none)"],
  "required_documents": ["documents or proofs the reader must provide (empty if none)"],
  "important_dates_amounts": ["deadlines, dates, fees, penalties, amounts"],
  "next_steps": ["what the reader should do, in order"],
  "unclear": ["important things the document does not say or that are ambiguous"]
}}"""

DOC_RULES = """You are JanSahayak AI. Explain the following official document in simple language for an ordinary citizen.
Use ONLY what is written in the document. Do not add facts, deadlines, amounts or legal provisions that are not in it.
If something important is missing or unclear, list it under "unclear". You are not a lawyer; do not give legal advice.
Write ALL text values in {language}. Keep names, numbers, dates and amounts unchanged."""

_SENT_SPLIT = re.compile(r"(?<=[.!?।])\s+|\n+")
_DATE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b", re.I)
_AMOUNT = re.compile(r"(?:₹|Rs\.?|INR)\s?[\d,]+(?:\.\d+)?(?:\s?(?:lakh|crore))?|\b\d+(?:\.\d+)?\s?(?:percent|%)", re.I)
_DOC_WORDS = re.compile(r"aadhaar|aadhar|pan card|certificate|proof|passport|ration card|passbook|photo|mark ?sheet|receipt|identity", re.I)
_ACTION_WORDS = re.compile(r"\b(apply|submit|visit|contact|pay|produce|fill|register|forward|verify)\b", re.I)
_BENEFIT_WORDS = re.compile(r"\b(benefit|receive|rebate|scholarship|assistance|grant|subsidy|credited|eligible)\b", re.I)
_KEY_WORDS = re.compile(r"\b(must|shall|required|last date|deadline|penalty|fee|liable|eligible|within|before|objection)\b", re.I)


_ABBREV = re.compile(r"\b(Rs|No|Ref|Sr|Dr|Mr|Mrs|Ms|approx)\.\s+", re.I)


def _sentences(text: str) -> list[str]:
    # Protect abbreviations such as "Rs. 50" from being split at the full stop.
    text = _ABBREV.sub(lambda m: m.group(1) + ".\x01", text)
    out = []
    for s in _SENT_SPLIT.split(text):
        s = re.sub(r"\s+", " ", s.replace("\x01", " ")).strip(" -*#")
        if len(s) > 15 and not s.startswith("***"):
            out.append(s)
    return out


def _uniq(items: list[str], limit: int) -> list[str]:
    seen, out = set(), []
    for i in items:
        key = i.lower()
        if key not in seen:
            seen.add(key)
            out.append(i if len(i) <= 300 else i[:297] + "...")
        if len(out) >= limit:
            break
    return out


def _offline_analysis(text: str) -> dict[str, Any]:
    sents = _sentences(text)
    dates_amounts = [m.group(0) for s in sents for m in list(_DATE.finditer(s)) + list(_AMOUNT.finditer(s))]
    return {
        "summary": " ".join(sents[:3])[:500] if sents else "",
        "key_points": _uniq([s for s in sents if _KEY_WORDS.search(s)], 6),
        "benefits": _uniq([s for s in sents if _BENEFIT_WORDS.search(s)], 4),
        "required_documents": _uniq([s for s in sents if _DOC_WORDS.search(s)], 6),
        "important_dates_amounts": _uniq(dates_amounts, 10),
        "next_steps": _uniq([s for s in sents if _ACTION_WORDS.search(s)], 5),
        "unclear": [],
    }


async def analyze_document(text: str, filename: str, language: str, settings: Settings) -> dict[str, Any]:
    client = GeminiClient(settings)
    if not text.strip():
        return {"analysis": _offline_analysis(""), "mode": "offline", "notice": "No readable text was found, so nothing could be explained."}
    if not client.enabled:
        return {"analysis": _offline_analysis(text), "mode": "offline",
                "notice": "Gemini is not configured, so this is a basic extraction (in the document's own language) rather than a simplified explanation."}

    system = DOC_RULES.format(language=_lang_name(language)) + "\n\n" + DOC_FORMAT
    try:
        raw = await client.generate(system, [user_turn(f"DOCUMENT ({filename}):\n{text[:30000]}")], json_mode=True, max_output_tokens=3000)
    except GeminiError as e:
        return {"analysis": _offline_analysis(text), "mode": "offline", "notice": f"{e} Showing a basic extraction instead."}

    parsed = parse_json(raw) or {}
    analysis = {
        "summary": str(parsed.get("summary") or raw[:600]).strip(),
        "key_points": _as_str_list(parsed.get("key_points")),
        "benefits": _as_str_list(parsed.get("benefits")),
        "required_documents": _as_str_list(parsed.get("required_documents")),
        "important_dates_amounts": _as_str_list(parsed.get("important_dates_amounts"), 12),
        "next_steps": _as_str_list(parsed.get("next_steps")),
        "unclear": _as_str_list(parsed.get("unclear")),
    }
    return {"analysis": analysis, "mode": "gemini", "notice": None}


# ---------- public: eligibility explanation & translation ----------

async def explain_eligibility(result: dict[str, Any], language: str, settings: Settings) -> str | None:
    """Plain-language summary of the rule-based result. Returns None when Gemini is unavailable."""
    client = GeminiClient(settings)
    if not client.enabled:
        return None
    lines = []
    for r in result["results"]:
        lines.append(f"- {r['scheme_name']}: {r['status']}. " + "; ".join(f"{c['label']} = {c['state']}" for c in r["criteria"]))
    system = (
        "You explain eligibility check results to ordinary citizens in simple language. "
        "Use ONLY the results given; do not add or change any criteria. Never promise approval; say 'may qualify' and "
        "that they must verify on the official website. Mention which schemes may fit, which do not and why, and which "
        f"need more details. Keep it under 150 words. Write in {_lang_name(language)}. Keep scheme names unchanged."
    )
    try:
        return await client.generate(system, [user_turn("RESULTS:\n" + "\n".join(lines))])
    except GeminiError:
        return None


async def translate(text: str, target_language: str, settings: Settings) -> str:
    client = GeminiClient(settings)
    if not client.enabled:
        raise GeminiError("Translation needs the Gemini API key to be configured on the server.")
    system = (
        f"Translate the user's text into {_lang_name(target_language)}. Keep numbers, names, URLs and markdown bullets unchanged. "
        "Output only the translation."
    )
    return await client.generate(system, [user_turn(text[:8000])], temperature=0.1, max_output_tokens=3000)
