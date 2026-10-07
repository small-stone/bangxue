"""Chat session store tests (memory backend + optional Postgres)."""

from __future__ import annotations

import os

import pytest

from app import session_store


@pytest.fixture(autouse=True)
def _memory_backend():
    session_store.use_memory_backend(True)
    yield
    session_store.use_memory_backend(False)


def test_missing_database_url_raises(monkeypatch):
    session_store.use_memory_backend(False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(session_store.SessionStoreError, match="DATABASE_URL"):
        session_store.database_url()


def test_save_load_exists_roundtrip():
    tid = "sess-test-1"
    payload = {
        "messages": [{"role": "user", "content": "hi"}],
        "draft": {"questions": [{"stem": "1+1"}]},
        "summary": "sum",
        "meta": {"grade": "一年级"},
    }
    session_store.save_session(tid, payload)
    assert session_store.session_exists(tid)
    loaded = session_store.load_session(tid)
    assert loaded is not None
    assert loaded["messages"] == payload["messages"]
    assert loaded["draft"] == payload["draft"]
    assert loaded["summary"] == "sum"
    assert loaded["meta"]["grade"] == "一年级"


def test_load_missing_returns_none():
    assert session_store.load_session("missing-thread") is None
    assert not session_store.session_exists("missing-thread")


@pytest.mark.skipif(
    not (os.environ.get("DATABASE_URL") or "").strip(),
    reason="DATABASE_URL not set",
)
def test_postgres_upsert_and_reload(monkeypatch):
    session_store.use_memory_backend(False)
    session_store.ensure_schema()
    tid = "pg-sess-" + os.urandom(4).hex()
    session_store.save_session(
        tid,
        {
            "messages": [{"role": "user", "content": "pg"}],
            "draft": None,
            "summary": "s",
            "meta": {},
        },
    )
    loaded = session_store.load_session(tid)
    assert loaded is not None
    assert loaded["messages"][0]["content"] == "pg"
