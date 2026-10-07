"""Quiz paper store tests (memory backend + TTL)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app import quiz_store


@pytest.fixture(autouse=True)
def _memory_backend():
    quiz_store.use_memory_backend(True)
    yield
    quiz_store.use_memory_backend(False)


def test_missing_database_url_raises(monkeypatch):
    quiz_store.use_memory_backend(False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(quiz_store.QuizStoreError, match="DATABASE_URL"):
        quiz_store.database_url()


def test_save_then_clear_cache_still_loads():
    quiz_id = quiz_store.save_quiz(
        {
            "title": "t",
            "questions": [{"stem": "2+2", "answer": "4"}],
            "include_answers": True,
            "meta": {"source": "test"},
        }
    )
    quiz_store.clear_cache()
    loaded = quiz_store.get_quiz(quiz_id)
    assert loaded is not None
    assert loaded["title"] == "t"
    assert loaded["questions"][0]["stem"] == "2+2"


def test_expired_returns_none():
    quiz_id = quiz_store.save_quiz(
        {"title": "old", "questions": [], "include_answers": False, "meta": {}}
    )
    # Force expire in memory backend
    assert quiz_store._MEMORY is not None
    quiz_store._MEMORY[quiz_id]["expires_at"] = datetime.now(timezone.utc) - timedelta(
        hours=1
    )
    quiz_store.clear_cache()
    assert quiz_store.get_quiz(quiz_id) is None
