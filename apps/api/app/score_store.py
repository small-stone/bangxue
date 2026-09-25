"""Local JSON score store and answer-sheet upload paths."""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

_LOCK = threading.Lock()

# apps/api/data — kept out of git via .gitignore
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
SCORES_PATH = DATA_DIR / "scores.json"


def ensure_data_dirs() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    if not SCORES_PATH.exists():
        SCORES_PATH.write_text(json.dumps({"attempts": {}}, ensure_ascii=False, indent=2), encoding="utf-8")


def _read() -> dict:
    ensure_data_dirs()
    try:
        raw = SCORES_PATH.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else {"attempts": {}}
    except (OSError, json.JSONDecodeError):
        data = {"attempts": {}}
    if "attempts" not in data or not isinstance(data["attempts"], dict):
        data = {"attempts": {}}
    return data


def _write(data: dict) -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SCORES_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(SCORES_PATH)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
        "photo_paths": payload.get("photo_paths") or [],
        "created_at": _now(),
        "confirmed_at": None,
    }
    with _LOCK:
        data = _read()
        data["attempts"][attempt_id] = record
        _write(data)
    return dict(record)


def get_attempt(attempt_id: str) -> dict | None:
    with _LOCK:
        data = _read()
        row = data["attempts"].get(attempt_id)
        return dict(row) if row else None


def confirm_attempt(attempt_id: str, email: str) -> dict | None:
    """Mark attempt confirmed and attach email. Returns None if missing."""
    email = email.strip().lower()
    if not email or "@" not in email:
        raise ValueError("invalid email")
    with _LOCK:
        data = _read()
        row = data["attempts"].get(attempt_id)
        if row is None:
            return None
        row["email"] = email
        row["confirmed"] = True
        row["confirmed_at"] = _now()
        data["attempts"][attempt_id] = row
        _write(data)
        return dict(row)


def list_confirmed_scores(email: str) -> list[dict]:
    email = email.strip().lower()
    with _LOCK:
        data = _read()
        rows = [
            dict(row)
            for row in data["attempts"].values()
            if row.get("confirmed") and (row.get("email") or "").lower() == email
        ]
    rows.sort(key=lambda r: r.get("confirmed_at") or r.get("created_at") or "", reverse=True)
    return rows


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
