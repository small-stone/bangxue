"""Supervisor graph wiring tests (injectable checkpointer + router)."""

from __future__ import annotations

import inspect

from langgraph.checkpoint.memory import InMemorySaver

from agents.chat import harness as chat_harness
from agents.supervisor.graph import (
    SUPERVISOR_CHECKPOINT_NS,
    build_supervisor_graph,
    run_supervisor,
)
from agents.supervisor.route import RouteDecision
from app import session_store


def setup_function() -> None:
    session_store.use_memory_backend(True)
    chat_harness._SESSIONS.clear()


def teardown_function() -> None:
    chat_harness._SESSIONS.clear()
    session_store.use_memory_backend(False)


def _seed_session() -> str:
    thread_id = f"sup-test-{len(chat_harness._SESSIONS) + 1}-{id(object())}"
    payload = {
        "messages": [],
        "draft": None,
        "summary": "",
        "meta": {},
    }
    session_store.save_session(thread_id, payload)
    chat_harness._SESSIONS[thread_id] = payload
    return thread_id


def test_build_graph_nodes_and_postgres_default():
    src = inspect.getsource(build_supervisor_graph)
    assert "get_checkpointer" in src
    assert "else get_checkpointer()" in " ".join(src.split())
    g = build_supervisor_graph(checkpointer=InMemorySaver())
    names = set(g.get_graph().nodes)
    assert {"route", "clarify", "chat_draft", "textbook_quiz"} <= names


def test_supervisor_checkpoint_ns_isolated_from_chat():
    assert SUPERVISOR_CHECKPOINT_NS == "supervisor"
    assert SUPERVISOR_CHECKPOINT_NS != chat_harness.CHAT_CHECKPOINT_NS
    src = inspect.getsource(run_supervisor)
    assert "SUPERVISOR_CHECKPOINT_NS" in src
    assert "checkpoint_ns" in src


def test_clarify_path_no_questions():
    thread_id = _seed_session()
    out = run_supervisor(
        thread_id,
        "出点数学题",
        router=lambda _t: RouteDecision(
            route="clarify",
            follow_up="请补充题量（1–100 道）和知识点。",
        ),
        checkpointer=InMemorySaver(),
    )
    assert out["status"] == "clarifying"
    assert not out.get("questions")
    assert "1–100" in out["assistant_text"] or "题量" in out["assistant_text"]


def test_textbook_path_missing_unit_clarifies():
    thread_id = _seed_session()
    out = run_supervisor(
        thread_id,
        "一年级上册不存在的单元XYZ出 10 道",
        router=lambda _t: RouteDecision(
            route="textbook_quiz",
            count=10,
            grade="一年级",
            term="上册",
            units=["不存在的单元XYZ"],
            summary="test",
        ),
        checkpointer=InMemorySaver(),
    )
    assert out["status"] == "clarifying"
    assert not out.get("questions")
