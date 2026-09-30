"""PostgreSQL grade attempts + local answer-sheet uploads.

Authoritative score storage is Postgres (`grade_attempts`). Answer photos stay
on local disk under `data/uploads/`; only relative paths are stored in the DB.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

logger = logging.getLogger(__name__)

# apps/api/data — kept out of git via .gitignore
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
LEGACY_SCORES_PATH = DATA_DIR / "scores.json"

_TABLE = "grade_attempts"


class ScoreStoreError(RuntimeError):
    """Database unavailable or misconfigured for score persistence."""


def database_url() -> str:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        raise ScoreStoreError("未配置 DATABASE_URL，无法读写成绩与答卷记录。")
    return url


def connect() -> psycopg.Connection:
    try:
        return psycopg.connect(database_url(), row_factory=dict_row)
    except ScoreStoreError:
        raise
    except Exception as exc:
        raise ScoreStoreError(f"无法连接成绩数据库：{exc}") from exc


def ensure_data_dirs() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def ensure_schema() -> None:
    """Create grade_attempts if missing. Fail closed when DB is unavailable."""
    ensure_data_dirs()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {_TABLE} (
                    id text PRIMARY KEY,
                    email text NULL,
                    confirmed boolean NOT NULL DEFAULT false,
                    demo boolean NOT NULL DEFAULT false,
                    quiz_id text NULL,
                    source text,
                    subject text,
                    title text,
                    correct integer NOT NULL,
                    total integer NOT NULL,
                    items jsonb NOT NULL DEFAULT '[]'::jsonb,
                    photo_paths text[] NOT NULL DEFAULT '{{}}',
                    created_at timestamptz NOT NULL,
                    confirmed_at timestamptz NULL
                )
                """
            )
            cur.execute(
                f"""
                CREATE INDEX IF NOT EXISTS grade_attempts_email_confirmed_idx
                ON {_TABLE} (email, confirmed, confirmed_at DESC)
                """
            )
        conn.commit()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _row_to_record(row: dict) -> dict:
    items = row.get("items") or []
    if isinstance(items, str):
        items = json.loads(items)
    photo_paths = row.get("photo_paths") or []
    if photo_paths is None:
        photo_paths = []
    created = row.get("created_at")
    confirmed_at = row.get("confirmed_at")
    return {
        "id": row["id"],
        "email": row.get("email"),
        "confirmed": bool(row.get("confirmed")),
        "demo": bool(row.get("demo")),
        "quiz_id": row.get("quiz_id"),
        "source": row.get("source"),
        "subject": row.get("subject"),
        "title": row.get("title"),
        "correct": int(row["correct"]),
        "total": int(row["total"]),
        "items": list(items),
        "photo_paths": list(photo_paths),
        "created_at": created.isoformat() if hasattr(created, "isoformat") else created,
        "confirmed_at": (
            confirmed_at.isoformat() if hasattr(confirmed_at, "isoformat") and confirmed_at else confirmed_at
        ),
    }


def save_upload(filename: str, content: bytes) -> str:
    """Persist one photo; return path relative to DATA_DIR."""
    ensure_data_dirs()
    safe = Path(filename).name or "photo.jpg"
    ext = safe.rsplit(".", 1)[-1].lower() if "." in safe else "jpg"
    if ext not in {"jpg", "jpeg", "png", "webp", "heic"}:
        ext = "jpg"
    name = f"{uuid4().hex}.{ext}"
    path = UPLOADS_DIR / name
    path.write_bytes(content)
    return f"uploads/{name}"


def create_attempt(payload: dict) -> dict:
    """Create an unconfirmed grading attempt. Returns the stored record."""
    attempt_id = uuid4().hex
    created = _now()
    record = {
        "id": attempt_id,
        "email": None,
        "confirmed": False,
        "demo": bool(payload.get("demo", False)),
        "quiz_id": payload.get("quiz_id"),
        "source": payload.get("source") or "textbook",
        "subject": payload.get("subject") or "数学",
        "title": payload.get("title") or "练习",
        "correct": int(payload["correct"]),
        "total": int(payload["total"]),
        "items": payload.get("items") or [],
        "photo_paths": list(payload.get("photo_paths") or []),
        "created_at": created,
        "confirmed_at": None,
    }
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {_TABLE} (
                    id, email, confirmed, demo, quiz_id, source, subject, title,
                    correct, total, items, photo_paths, created_at, confirmed_at
                ) VALUES (
                    %(id)s, %(email)s, %(confirmed)s, %(demo)s, %(quiz_id)s, %(source)s,
                    %(subject)s, %(title)s, %(correct)s, %(total)s, %(items)s,
                    %(photo_paths)s, %(created_at)s, %(confirmed_at)s
                )
                """,
                {
                    **record,
                    "items": Jsonb(record["items"]),
                },
            )
        conn.commit()
    return _row_to_record(record)


def get_attempt(attempt_id: str) -> dict | None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {_TABLE} WHERE id = %s", (attempt_id,))
            row = cur.fetchone()
    return _row_to_record(row) if row else None


def confirm_attempt(attempt_id: str, email: str) -> dict | None:
    """Mark attempt confirmed and attach email. Returns None if missing."""
    email = email.strip().lower()
    if not email or "@" not in email:
        raise ValueError("invalid email")
    confirmed_at = _now()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE {_TABLE}
                SET email = %s, confirmed = true, confirmed_at = %s
                WHERE id = %s
                RETURNING *
                """,
                (email, confirmed_at, attempt_id),
            )
            row = cur.fetchone()
        conn.commit()
    return _row_to_record(row) if row else None


def list_confirmed_scores(email: str) -> list[dict]:
    email = email.strip().lower()
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT * FROM {_TABLE}
                WHERE confirmed = true AND lower(email) = %s
                ORDER BY confirmed_at DESC NULLS LAST, created_at DESC
                """,
                (email,),
            )
            rows = cur.fetchall()
    return [_row_to_record(row) for row in rows]


def list_wrong_questions(email: str) -> list[dict]:
    """Aggregate wrong items from confirmed attempts for one parent."""
    out: list[dict] = []
    for attempt in list_confirmed_scores(email):
        for item in attempt.get("items") or []:
            if item.get("correct"):
                continue
            out.append(
                {
                    "attempt_id": attempt["id"],
                    "subject": attempt.get("subject"),
                    "title": attempt.get("title"),
                    "source": attempt.get("source"),
                    "date": (attempt.get("confirmed_at") or attempt.get("created_at") or "")[:10],
                    "index": item.get("index"),
                    "stem": item.get("stem"),
                    "answer": item.get("answer"),
                    "student_answer": item.get("student_answer"),
                }
            )
    return out


def import_legacy_scores_json(*, path: Path | None = None) -> int:
    """One-shot import from legacy scores.json. Skip existing ids. Return inserted count."""
    src = path or LEGACY_SCORES_PATH
    if not src.is_file():
        return 0
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Skip legacy scores import: %s", exc)
        return 0
    attempts = raw.get("attempts") if isinstance(raw, dict) else None
    if not isinstance(attempts, dict) or not attempts:
        return 0

    inserted = 0
    with connect() as conn:
        with conn.cursor() as cur:
            for attempt_id, row in attempts.items():
                if not isinstance(row, dict):
                    continue
                cur.execute(f"SELECT 1 FROM {_TABLE} WHERE id = %s", (attempt_id,))
                if cur.fetchone():
                    continue
                created_raw = row.get("created_at") or _now().isoformat()
                confirmed_raw = row.get("confirmed_at")
                cur.execute(
                    f"""
                    INSERT INTO {_TABLE} (
                        id, email, confirmed, demo, quiz_id, source, subject, title,
                        correct, total, items, photo_paths, created_at, confirmed_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::timestamptz, %s::timestamptz
                    )
                    """,
                    (
                        str(row.get("id") or attempt_id),
                        row.get("email"),
                        bool(row.get("confirmed")),
                        bool(row.get("demo", False)),
                        row.get("quiz_id"),
                        row.get("source") or "textbook",
                        row.get("subject") or "数学",
                        row.get("title") or "练习",
                        int(row.get("correct") or 0),
                        int(row.get("total") or 0),
                        Jsonb(row.get("items") or []),
                        list(row.get("photo_paths") or []),
                        created_raw,
                        confirmed_raw,
                    ),
                )
                inserted += 1
        conn.commit()
    if inserted:
        logger.info("Imported %s legacy grade attempts from %s", inserted, src)
    return inserted


def bootstrap_score_store() -> None:
    """Ensure dirs, schema, and optional one-shot JSON import."""
    ensure_data_dirs()
    ensure_schema()
    try:
        import_legacy_scores_json()
    except ScoreStoreError:
        raise
    except Exception as exc:
        logger.warning("Legacy scores import failed: %s", exc)
