"""LangGraph supervisor: route → clarify | chat_draft | textbook_quiz."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Callable, NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.shared.checkpointer import get_checkpointer
from agents.supervisor.route import RouteDecision, decide_route, decision_to_meta

# Distinct from chat harness (`chat-agent`) so shared thread_id does not collide.
SUPERVISOR_CHECKPOINT_NS = "supervisor"

RouterFn = Callable[[str], RouteDecision]

# Test/injectable router — never stored in graph state (must stay msgpack-safe).
_ROUTER: ContextVar[RouterFn | None] = ContextVar("supervisor_router", default=None)


class SupervisorState(TypedDict):
    thread_id: str
    text: str
    transcript: str
    route: NotRequired[str]
    follow_up: NotRequired[str]
    summary: NotRequired[str]
    count: NotRequired[int | None]
    grade: NotRequired[str]
    subject: NotRequired[str]
    term: NotRequired[str]
    edition: NotRequired[str]
    units: NotRequired[list[str]]
    difficulty: NotRequired[str]
    reason: NotRequired[str]
    status: NotRequired[str]
    assistant_text: NotRequired[str]
    questions: NotRequired[list[dict]]
    meta: NotRequired[dict[str, Any]]


def _decision_from_state(state: SupervisorState) -> RouteDecision:
    return RouteDecision(
        route=state.get("route") or "clarify",  # type: ignore[arg-type]
        follow_up=state.get("follow_up") or "",
        summary=state.get("summary") or "",
        count=state.get("count"),
        grade=state.get("grade") or "",
        subject=state.get("subject") or "数学",
        term=state.get("term") or "上册",
        edition=state.get("edition") or "人教版",
        units=list(state.get("units") or []),
        difficulty=state.get("difficulty") or "适中",
        reason=state.get("reason") or "",
    )


def _route_node(state: SupervisorState) -> dict[str, Any]:
    decision = decide_route(
        state.get("transcript") or state.get("text") or "",
        router=_ROUTER.get(),
    )
    return {
        "route": decision.route,
        "follow_up": decision.follow_up,
        "summary": decision.summary,
        "count": decision.count,
        "grade": decision.grade,
        "subject": decision.subject,
        "term": decision.term,
        "edition": decision.edition,
        "units": decision.units,
        "difficulty": decision.difficulty,
        "reason": decision.reason,
        "meta": decision_to_meta(decision),
    }


def _clarify_node(state: SupervisorState) -> dict[str, Any]:
    from agents.chat.harness import apply_clarify

    decision = _decision_from_state(state)
    result = apply_clarify(state["thread_id"], decision)
    return {
        "status": result.status,
        "assistant_text": result.assistant_text,
        "questions": result.questions,
        "summary": result.summary,
        "meta": result.meta,
    }


def _chat_draft_node(state: SupervisorState) -> dict[str, Any]:
    from agents.chat.harness import apply_chat_draft

    decision = _decision_from_state(state)
    result = apply_chat_draft(state["thread_id"], state.get("transcript") or "", decision)
    return {
        "status": result.status,
        "assistant_text": result.assistant_text,
        "questions": result.questions,
        "summary": result.summary,
        "meta": result.meta,
    }


def _textbook_quiz_node(state: SupervisorState) -> dict[str, Any]:
    from agents.chat.harness import apply_textbook_quiz

    decision = _decision_from_state(state)
    result = apply_textbook_quiz(state["thread_id"], decision)
    return {
        "status": result.status,
        "assistant_text": result.assistant_text,
        "questions": result.questions,
        "summary": result.summary,
        "meta": result.meta,
    }


def _branch(state: SupervisorState) -> str:
    route = state.get("route") or "clarify"
    if route == "chat_draft":
        return "chat_draft"
    if route == "textbook_quiz":
        return "textbook_quiz"
    return "clarify"


def build_supervisor_graph(*, checkpointer: Any | None = None):
    """Compile supervisor graph. Production path uses Postgres checkpointer."""
    graph = StateGraph(SupervisorState)
    graph.add_node("route", _route_node)
    graph.add_node("clarify", _clarify_node)
    graph.add_node("chat_draft", _chat_draft_node)
    graph.add_node("textbook_quiz", _textbook_quiz_node)
    graph.add_edge(START, "route")
    graph.add_conditional_edges(
        "route",
        _branch,
        {
            "clarify": "clarify",
            "chat_draft": "chat_draft",
            "textbook_quiz": "textbook_quiz",
        },
    )
    graph.add_edge("clarify", END)
    graph.add_edge("chat_draft", END)
    graph.add_edge("textbook_quiz", END)

    saver = checkpointer if checkpointer is not None else get_checkpointer()
    # Production default is Postgres via get_checkpointer(); do not default to in-memory.
    return graph.compile(checkpointer=saver)


def run_supervisor(
    thread_id: str,
    text: str,
    *,
    transcript: str | None = None,
    router: RouterFn | None = None,
    checkpointer: Any | None = None,
) -> dict[str, Any]:
    """Invoke supervisor and return output state fields for ChatTurnResult."""
    state: SupervisorState = {
        "thread_id": thread_id,
        "text": text,
        "transcript": transcript if transcript is not None else text,
    }
    token = _ROUTER.set(router)
    try:
        graph = build_supervisor_graph(checkpointer=checkpointer)
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": SUPERVISOR_CHECKPOINT_NS,
            }
        }
        return graph.invoke(state, config=config)
    finally:
        _ROUTER.reset(token)
