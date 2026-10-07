"""Unit tests for closed-set supervisor routing."""

from __future__ import annotations

from agents.supervisor.route import RouteDecision, decide_route


def test_empty_clarifies():
    d = decide_route("")
    assert d.route == "clarify"
    assert d.follow_up


def test_vague_math_clarifies():
    d = decide_route("出点数学题")
    assert d.route == "clarify"
    assert "1–100" in d.follow_up or "1-100" in d.follow_up or "题量" in d.follow_up


def test_chat_draft_heuristic():
    d = decide_route("三年级口算 12 道")
    assert d.route == "chat_draft"
    assert d.count == 12
    assert d.grade == "三年级"


def test_textbook_heuristic():
    d = decide_route("一年级上册数学游戏出 10 道")
    assert d.route == "textbook_quiz"
    assert d.count == 10
    assert d.grade == "一年级"
    assert any("数学游戏" in u for u in d.units)


def test_count_over_100_clarifies():
    d = decide_route("三年级口算 101 道")
    assert d.route == "clarify"


def test_router_inject_and_invalid_fallback():
    d = decide_route(
        "anything",
        router=lambda _t: RouteDecision(route="nope", follow_up="请补充"),  # type: ignore[arg-type]
    )
    assert d.route == "clarify"


def test_injected_routes():
    d = decide_route(
        "x",
        router=lambda _t: RouteDecision(route="chat_draft", count=10, grade="一年级", summary="x"),
    )
    assert d.route == "chat_draft"
    d2 = decide_route(
        "x",
        router=lambda _t: RouteDecision(
            route="textbook_quiz",
            count=10,
            grade="一年级",
            units=["数学游戏"],
        ),
    )
    assert d2.route == "textbook_quiz"
