"""Chat harness session persistence + checkpoint namespace."""

from __future__ import annotations

import inspect

import pytest

from agents.chat import harness
from app import session_store


@pytest.fixture(autouse=True)
def _memory_session():
    session_store.use_memory_backend(True)
    harness._SESSIONS.clear()
    yield
    harness._SESSIONS.clear()
    session_store.use_memory_backend(False)


def test_chat_checkpoint_ns_constant_and_create_uses_it():
    assert harness.CHAT_CHECKPOINT_NS == "chat-agent"
    src = inspect.getsource(harness.create_session)
    assert 'checkpoint_ns": CHAT_CHECKPOINT_NS' in src.replace(" ", "") or (
        "CHAT_CHECKPOINT_NS" in src and "checkpoint_ns" in src
    )
    draft_src = inspect.getsource(harness._draft_via_agent)
    assert "CHAT_CHECKPOINT_NS" in draft_src
    assert 'checkpoint_ns": ""' not in inspect.getsource(harness)


def test_session_survives_cache_clear():
    # Bypass checkpointer seed — only session store path.
    tid = "harness-persist-1"
    session_store.save_session(
        tid,
        {
            "messages": [{"role": "user", "content": "出题"}],
            "draft": {"questions": [{"stem": "1"}]},
            "summary": "s",
            "meta": {"k": 1},
        },
    )
    harness._SESSIONS.clear()
    assert harness.session_exists(tid)
    loaded = harness.get_session(tid)
    assert loaded["draft"]["questions"][0]["stem"] == "1"
    assert loaded["messages"][0]["content"] == "出题"


def test_missing_session_404():
    with pytest.raises(harness.ChatError) as exc:
        harness.get_session("no-such-thread")
    assert exc.value.status_code == 404
