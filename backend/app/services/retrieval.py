"""Small, dependency-free retrieval layer (BM25) for RAG.

Two kinds of chunks are searched:
  * knowledge-base chunks (schemes and rights, each with an official URL)
  * chunks of a document the user uploaded

The tokenizer keeps Devanagari combining marks so Hindi and Marathi words stay intact.
"""
from __future__ import annotations

import math
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from . import knowledge

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "to", "of", "and", "or", "in", "on", "for",
    "with", "i", "me", "my", "we", "you", "your", "it", "this", "that", "can", "do", "does", "how",
    "what", "who", "when", "where", "which", "will", "if", "at", "by", "from", "as", "about", "get",
    "है", "हैं", "का", "की", "के", "में", "से", "को", "और", "या", "यह", "वह", "कि", "पर", "क्या", "कैसे",
    "आहे", "आणि", "का", "ला", "ची", "चा", "चे", "मध्ये", "काय", "कसे", "हे", "ते",
}


@dataclass
class Chunk:
    id: str
    text: str
    kind: str  # "scheme" | "right" | "uploaded"
    title: str
    url: str = ""
    section: str = ""
    ref_id: str = ""  # scheme/right id or document id
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Hit:
    chunk: Chunk
    score: float


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    buf: list[str] = []
    for ch in text.lower():
        cat = unicodedata.category(ch)
        if cat[0] in ("L", "N", "M"):
            buf.append(ch)
        elif buf:
            tokens.append("".join(buf))
            buf = []
    if buf:
        tokens.append("".join(buf))
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


class BM25Index:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        self.docs = [tokenize(c.text + " " + c.title) for c in chunks]
        self.tf = [Counter(d) for d in self.docs]
        self.doc_len = [len(d) for d in self.docs]
        self.avg_len = (sum(self.doc_len) / len(self.doc_len)) if self.docs else 0.0
        df: Counter[str] = Counter()
        for d in self.docs:
            df.update(set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, k: int = 4) -> list[Hit]:
        q = tokenize(query)
        if not q or not self.docs:
            return []
        hits: list[Hit] = []
        for i, tf in enumerate(self.tf):
            score = 0.0
            for term in q:
                f = tf.get(term)
                if not f:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * self.doc_len[i] / (self.avg_len or 1))
                score += self.idf.get(term, 0.0) * (f * (self.k1 + 1)) / denom
            if score > 0:
                hits.append(Hit(self.chunks[i], score))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:k]


# ---------- knowledge base chunks ----------

def _scheme_chunk(s: dict[str, Any]) -> Chunk:
    text = " ".join(
        [
            s["name"], s["summary"],
            "Benefits: " + "; ".join(s["benefits"]),
            "Eligibility: " + "; ".join(s["eligibility_text"]),
            "Documents: " + "; ".join(s["required_documents"]),
            "How to apply: " + "; ".join(s["how_to_apply"]),
            " ".join(s.get("keywords", [])),
        ]
    )
    return Chunk(
        id=f"scheme:{s['id']}", text=text, kind="scheme", title=s["name"],
        url=s["official_url"], section=s["source_name"], ref_id=s["id"],
        meta={"data_status": s.get("data_status", "sample")},
    )


def _right_chunk(r: dict[str, Any]) -> Chunk:
    text = " ".join(
        [
            r["title"], r["summary"], " ".join(r["key_points"]), " ".join(r["what_to_do"]),
            r.get("law", ""), " ".join(r.get("keywords", [])),
        ]
    )
    return Chunk(
        id=f"right:{r['id']}", text=text, kind="right", title=r["title"],
        url=r["official_url"], section=r.get("law", r["source_name"]), ref_id=r["id"],
        meta={"data_status": r.get("data_status", "sample")},
    )


@lru_cache(maxsize=1)
def kb_index() -> BM25Index:
    chunks = [_scheme_chunk(s) for s in knowledge.list_schemes()]
    chunks += [_right_chunk(r) for r in knowledge.list_rights()]
    return BM25Index(chunks)


# ---------- uploaded document chunks ----------

def chunk_text(text: str, size: int = 900, overlap: int = 150) -> list[str]:
    """Split on paragraph boundaries into overlapping windows of roughly `size` characters."""
    paras = [p.strip() for p in text.replace("\r", "").split("\n") if p.strip()]
    chunks: list[str] = []
    cur = ""
    for p in paras:
        if len(p) > size:  # very long paragraph: hard split
            if cur:
                chunks.append(cur)
                cur = ""
            for i in range(0, len(p), size - overlap):
                chunks.append(p[i : i + size])
            continue
        if len(cur) + len(p) + 1 > size and cur:
            chunks.append(cur)
            cur = cur[-overlap:] + " " + p if overlap else p
        else:
            cur = (cur + "\n" + p) if cur else p
    if cur:
        chunks.append(cur)
    return chunks


def document_chunks(doc_id: str, filename: str, text: str) -> list[Chunk]:
    out = []
    for i, part in enumerate(chunk_text(text), start=1):
        out.append(
            Chunk(
                id=f"doc:{doc_id}:{i}", text=part, kind="uploaded", title=filename,
                section=f"Part {i}", ref_id=doc_id,
            )
        )
    return out


def retrieve(query: str, doc: dict[str, Any] | None = None, k_kb: int = 3, k_doc: int = 4) -> list[Hit]:
    """Return KB hits and (optionally) hits from the user's uploaded document."""
    hits = kb_index().search(query, k=k_kb)
    if doc:
        index = BM25Index(document_chunks(doc["id"], doc["filename"], doc["text"]))
        doc_hits = index.search(query, k=k_doc)
        if not doc_hits and index.chunks:  # generic question about the document: use its opening
            doc_hits = [Hit(c, 0.01) for c in index.chunks[:2]]
        hits = doc_hits + hits
    return hits


MIN_KB_SCORE = 1.5  # below this, treat the KB as having no relevant answer


def is_relevant(hits: list[Hit]) -> bool:
    return bool(hits) and (hits[0].chunk.kind == "uploaded" or hits[0].score >= MIN_KB_SCORE)
