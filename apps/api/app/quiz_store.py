"""PostgreSQL quiz paper store with TTL.

Authoritative papers live in `quiz_papers`. Process memory is an optional cache.
Missing DATABASE_URL fails closed on save.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

logger = logging.getLogger(__name__)

_TABLE = "quiz_papers"
_CACHE: dict[str, dict] = {}

# When set, all ops use this dict instead of Postgres (unit tests).
_MEMORY: dict[str, dict[str, Any]] | None = None

DEFAULT_TTL_DAYS = 7


class QuizStoreError(RuntimeError):
    """Database unavailable or misconfigured for quiz persistence."""


def use_memory_backend(enabled: bool = True) -> None:
    """Enable/disable in-process memory backend (tests only)."""
    global _MEMORY
    _MEMORY = {} if enabled else None
    _CACHE.clear()


def clear_cache() -> None:
    """Drop process-local cache (tests / multi-worker simulation)."""
    _CACHE.clear()


def database_url() -> str:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        raise QuizStoreError("未配置 DATABASE_URL，无法读写练习卷。")
    return url


def connect() -> psycopg.Connection:
    try:
        return psycopg.connect(database_url(), row_factory=dict_row)
    except QuizStoreError:
        raise
    except Exception as exc:
        raise QuizStoreError(f"无法连接练习卷数据库：{exc}") from exc


def ttl_days() -> int:
    raw = (os.environ.get("QUIZ_PAPER_TTL_DAYS") or "").strip()
    if not raw:
        return DEFAULT_TTL_DAYS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_TTL_DAYS
    return max(1, value)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_schema() -> None:
    """Create quiz_papers if missing. Fail closed when DB is unavailable."""
    if _MEMORY is not None:
        return
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_TABLE} (
                    id text PRIMARY KEY,
                    payload jsonb NOT NULL,
                    include_answers boolean NOT NULL DEFAULT true,
                    meta jsonb NOT NULL DEFAULT '{{}}'::jsonb,
                    created_at timestamptz NOT NULL,
                    expires_at timestamptz NOT NULL
                )
                """
            )
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS quiz_papers_expires_at_idx
                ON {_TABLE} (expires_at)
                """
            )
        conn.commit()


def save_quiz(quiz: dict) -> str:
    quiz_id = uuid4().hex
    now = _now()
    expires = now + timedelta(days=ttl_days())
    payload = dict(quiz)
    include_answers = bool(payload.get("include_answers", True))
    meta = dict(payload.get("meta") or {})

    if _MEMORY is not None:
        _MEMORY[quiz_id] = {
            "payload": payload,
            "include_answers": include_answers,
            "meta": meta,
            "expires_at": expires,
        }
        _CACHE[quiz_id] = payload
        return quiz_id

    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_TABLE} (
                    id, payload, include_answers, meta, created_at, expires_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    quiz_id,
                    Jsonb(payload),
                    include_answers,
                    Jsonb(meta),
                    now,
                    expires,
                ),
            )
        conn.commit()
    _CACHE[quiz_id] = payload
    return quiz_id


def get_quiz(quiz_id: str) -> dict | None:
    if not quiz_id:
        return None
    cached = _CACHE.get(quiz_id)
    if cached is not None:
        return cached

    if _MEMORY is not None:
        row = _MEMORY.get(quiz_id)
        if not row:
            return None
        expires_at = row.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at <= _now():
            return None
        payload = dict(row["payload"])
        _CACHE[quiz_id] = payload
        return payload

    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT payload, expires_at
                    FROM {_TABLE}
                    WHERE id = %s
                    """,
                    (quiz_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                expires_at = row.get("expires_at")
                if expires_at is not None and expires_at <= _now():
                    return None
                payload = row.get("payload") or {}
                if isinstance(payload, str):
                    payload = json.loads(payload)
                payload = dict(payload)
                _CACHE[quiz_id] = payload
                return payload
    except QuizStoreError:
        raise
    except Exception as exc:
        raise QuizStoreError(f"无法读取练习卷：{exc}") from exc


def bootstrap_quiz_store() -> None:
    ensure_schema()
