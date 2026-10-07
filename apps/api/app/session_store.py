"""PostgreSQL chat session store (messages / draft / summary / meta).

Authoritative session state lives in `chat_sessions`. Process memory is an
optional cache only. Missing DATABASE_URL fails closed.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

logger = logging.getLogger(__name__)

_TABLE = "chat_sessions"

# When set, all ops use this dict instead of Postgres (unit tests).
_MEMORY: dict[str, dict[str, Any]] | None = None


class SessionStoreError(RuntimeError):
    """Database unavailable or misconfigured for chat session persistence."""


def use_memory_backend(enabled: bool = True) -> None:
    """Enable/disable in-process memory backend (tests only)."""
    global _MEMORY
    _MEMORY = {} if enabled else None


def clear_memory_backend() -> None:
    if _MEMORY is not None:
        _MEMORY.clear()


def database_url() -> str:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        raise SessionStoreError("未配置 DATABASE_URL，无法读写对话会话。")
    return url


def connect() -> psycopg.Connection:
    try:
        return psycopg.connect(database_url(), row_factory=dict_row)
    except SessionStoreError:
        raise
    except Exception as exc:
        raise SessionStoreError(f"无法连接对话会话数据库：{exc}") from exc


def _now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_schema() -> None:
    """Create chat_sessions if missing. Fail closed when DB is unavailable."""
    if _MEMORY is not None:
        return
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_TABLE} (
                    thread_id text PRIMARY KEY,
                    messages jsonb NOT NULL DEFAULT '[]'::jsonb,
                    draft jsonb NULL,
                    summary text NOT NULL DEFAULT '',
                    meta jsonb NOT NULL DEFAULT '{{}}'::jsonb,
                    created_at timestamptz NOT NULL,
                    updated_at timestamptz NOT NULL
                )
                """
            )
        conn.commit()


def empty_session() -> dict[str, Any]:
    return {"messages": [], "draft": None, "summary": "", "meta": {}}


def _row_to_session(row: dict) -> dict[str, Any]:
    messages = row.get("messages") or []
    if isinstance(messages, str):
        messages = json.loads(messages)
    draft = row.get("draft")
    if isinstance(draft, str):
        draft = json.loads(draft)
    meta = row.get("meta") or {}
    if isinstance(meta, str):
        meta = json.loads(meta)
    return {
        "messages": list(messages),
        "draft": draft,
        "summary": str(row.get("summary") or ""),
        "meta": dict(meta),
    }


def session_exists(thread_id: str) -> bool:
    if not thread_id:
        return False
    if _MEMORY is not None:
        return thread_id in _MEMORY
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT 1 FROM {_TABLE} WHERE thread_id = %s LIMIT 1",
                (thread_id,),
            )
            return cur.fetchone() is not None


def load_session(thread_id: str) -> dict[str, Any] | None:
    if not thread_id:
        return None
    if _MEMORY is not None:
        payload = _MEMORY.get(thread_id)
        return dict(payload) if payload is not None else None
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT thread_id, messages, draft, summary, meta
                FROM {_TABLE}
                WHERE thread_id = %s
                """,
                (thread_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return _row_to_session(row)


def save_session(thread_id: str, session: dict[str, Any]) -> None:
    """Upsert authoritative session payload."""
    if not thread_id:
        raise SessionStoreError("thread_id 不能为空。")
    messages = list(session.get("messages") or [])
    draft = session.get("draft")
    summary = str(session.get("summary") or "")
    meta = dict(session.get("meta") or {})
    now = _now()

    if _MEMORY is not None:
        _MEMORY[thread_id] = {
            "messages": messages,
            "draft": draft,
            "summary": summary,
            "meta": meta,
        }
        return

    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_TABLE} (
                    thread_id, messages, draft, summary, meta, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (thread_id) DO UPDATE SET
                    messages = EXCLUDED.messages,
                    draft = EXCLUDED.draft,
                    summary = EXCLUDED.summary,
                    meta = EXCLUDED.meta,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    thread_id,
                    Jsonb(messages),
                    Jsonb(draft) if draft is not None else None,
                    summary,
                    Jsonb(meta),
                    now,
                    now,
                ),
            )
        conn.commit()


def bootstrap_session_store() -> None:
    ensure_schema()
