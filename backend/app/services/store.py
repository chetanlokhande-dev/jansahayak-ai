"""SQLite persistence for conversation history and uploaded-document text.

Everything is scoped by an anonymous client id (a random UUID the browser creates), so users
only see their own history. Swap this module for Supabase/PostgreSQL when you add real accounts.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations (
  id TEXT PRIMARY KEY, client_id TEXT NOT NULL, title TEXT NOT NULL, language TEXT NOT NULL,
  document_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL,
  extra TEXT, created_at TEXT NOT NULL,
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY, client_id TEXT NOT NULL, filename TEXT NOT NULL, kind TEXT NOT NULL,
  method TEXT NOT NULL, text TEXT NOT NULL, analysis TEXT, language TEXT NOT NULL, warnings TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conv_client ON conversations(client_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_doc_client ON documents(client_id, created_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_id() -> str:
    return uuid.uuid4().hex


class Store:
    def __init__(self, path: Path | str):
        self.path = str(path)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    def _run(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            cur = self._conn.execute(sql, params)
            rows = cur.fetchall()
            self._conn.commit()
            return rows

    # ----- conversations -----
    def create_conversation(self, client_id: str, title: str, language: str, document_id: str | None = None) -> str:
        cid, now = _new_id(), _now()
        self._run(
            "INSERT INTO conversations VALUES (?,?,?,?,?,?,?)",
            (cid, client_id, title[:80], language, document_id, now, now),
        )
        return cid

    def get_conversation(self, client_id: str, conv_id: str) -> dict[str, Any] | None:
        rows = self._run("SELECT * FROM conversations WHERE id=? AND client_id=?", (conv_id, client_id))
        return dict(rows[0]) if rows else None

    def add_message(self, conv_id: str, role: str, content: str, extra: dict[str, Any] | None = None) -> str:
        mid = _new_id()
        self._run(
            "INSERT INTO messages VALUES (?,?,?,?,?,?)",
            (mid, conv_id, role, content, json.dumps(extra) if extra else None, _now()),
        )
        self._run("UPDATE conversations SET updated_at=? WHERE id=?", (_now(), conv_id))
        return mid

    def messages(self, conv_id: str) -> list[dict[str, Any]]:
        rows = self._run("SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at, rowid", (conv_id,))
        out = []
        for r in rows:
            item = {"id": r["id"], "role": r["role"], "content": r["content"], "created_at": r["created_at"]}
            if r["extra"]:
                item.update(json.loads(r["extra"]))
            out.append(item)
        return out

    def list_conversations(self, client_id: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._run(
            "SELECT id, title, language, document_id, created_at, updated_at FROM conversations "
            "WHERE client_id=? ORDER BY updated_at DESC LIMIT ?", (client_id, limit),
        )
        return [dict(r) for r in rows]

    def delete_conversation(self, client_id: str, conv_id: str) -> bool:
        if not self.get_conversation(client_id, conv_id):
            return False
        self._run("DELETE FROM messages WHERE conversation_id=?", (conv_id,))
        self._run("DELETE FROM conversations WHERE id=?", (conv_id,))
        return True

    # ----- documents -----
    def add_document(self, client_id: str, filename: str, kind: str, method: str, text: str,
                     analysis: dict[str, Any] | None, language: str, warnings: list[str]) -> str:
        did = _new_id()
        self._run(
            "INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?)",
            (did, client_id, filename, kind, method, text, json.dumps(analysis) if analysis else None,
             language, json.dumps(warnings), _now()),
        )
        return did

    def get_document(self, client_id: str, doc_id: str) -> dict[str, Any] | None:
        rows = self._run("SELECT * FROM documents WHERE id=? AND client_id=?", (doc_id, client_id))
        if not rows:
            return None
        r = dict(rows[0])
        r["analysis"] = json.loads(r["analysis"]) if r["analysis"] else None
        r["warnings"] = json.loads(r["warnings"]) if r["warnings"] else []
        return r

    def list_documents(self, client_id: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._run(
            "SELECT id, filename, kind, method, language, created_at, length(text) AS chars FROM documents "
            "WHERE client_id=? ORDER BY created_at DESC LIMIT ?", (client_id, limit),
        )
        return [dict(r) for r in rows]

    def delete_document(self, client_id: str, doc_id: str) -> bool:
        if not self.get_document(client_id, doc_id):
            return False
        self._run("DELETE FROM documents WHERE id=?", (doc_id,))
        return True

    def delete_all(self, client_id: str) -> None:
        for conv in self.list_conversations(client_id, limit=10_000):
            self.delete_conversation(client_id, conv["id"])
        self._run("DELETE FROM documents WHERE client_id=?", (client_id,))
