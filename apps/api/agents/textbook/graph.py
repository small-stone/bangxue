"""LangGraph StateGraph for Mode A textbook quiz generation."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.textbook.generate import (
    TextbookError,
    _bailian_generator,
    load_unit_text,
)
from app.question_format import normalize_options


class TextbookQuizState(TypedDict):
    meta: dict[str, str]
    units: list[str]
    source_text: NotRequired[str]
    count: int
    difficulty: str
    include_answers: bool
    grade: str
    questions: NotRequired[list[dict]]
    error: NotRequired[str]
    error_status: NotRequired[int]
    # Optional injectable generator for tests (not serializable across processes).
    generator: NotRequired[Any]


def _load_source_text(state: TextbookQuizState) -> dict[str, Any]:
    if state.get("error"):
        return {}
    if (state.get("source_text") or "").strip():
        return {}
    units = state.get("units") or []
    meta = state.get("meta") or {}
    try:
        text = load_unit_text(units, **meta)
    except TextbookError as exc:
        return {"error": str(exc), "error_status": exc.status_code}
    return {"source_text": text}


def _generate_questions(state: TextbookQuizState) -> dict[str, Any]:
    if state.get("error"):
        return {}
    count = state["count"]
    if count not in {10, 15, 20, 30}:
        return {"error": "题量只能是 10、15、20 或 30。", "error_status": 400}
    source_text = (state.get("source_text") or "").strip()
    if not source_text:
        return {"error": "所选单元没有可用课文。", "error_status": 404}

    build = state.get("generator") or _bailian_generator
    include_answers = bool(state["include_answers"])
    try:
        questions = build(
            source_text=source_text,
            count=count,
            difficulty=state["difficulty"],
            include_answers=include_answers,
            grade=state.get("grade") or "一年级",
        )
    except TextbookError as exc:
        return {"error": str(exc), "error_status": exc.status_code}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"暂时无法出题：{exc}", "error_status": 503}

    if len(questions) != count:
        return {"error": "题目数量与设置不一致，请重试。", "error_status": 502}

    cleaned: list[dict] = []
    for item in questions:
        stem = str(item.get("stem", "")).strip()
        if not stem:
            return {"error": "生成结果缺少题干。", "error_status": 502}
        qtype = str(item.get("qtype") or "计算题").strip() or "计算题"
        row: dict = {"qtype": qtype, "stem": stem}
        options = normalize_options(item.get("options"))
        if qtype == "选择题":
            if not options or len(options) < 2:
                return {"error": "选择题缺少选项，请重试。", "error_status": 502}
            row["options"] = options
        elif options:
            row["options"] = options
        if include_answers:
            row["answer"] = str(item.get("answer", "")).strip()
        cleaned.append(row)
    return {"questions": cleaned}


@lru_cache(maxsize=1)
def build_graph():
    """Compile the textbook quiz StateGraph (no checkpointer; one-shot invoke)."""
    graph = StateGraph(TextbookQuizState)
    graph.add_node("load_units_text", _load_source_text)
    graph.add_node("generate_json_questions", _generate_questions)
    graph.add_edge(START, "load_units_text")
    graph.add_edge("load_units_text", "generate_json_questions")
    graph.add_edge("generate_json_questions", END)
    return graph.compile()


def run_textbook_quiz(
    *,
    units: list[str],
    count: int,
    difficulty: str,
    include_answers: bool,
    generator: Any | None = None,
    source_text: str | None = None,
    **meta: str,
) -> list[dict]:
    """Invoke the textbook graph and raise TextbookError on failure."""
    state: TextbookQuizState = {
        "meta": {
            "stage": meta["stage"],
            "grade": meta["grade"],
            "subject": meta["subject"],
            "edition": meta["edition"],
            "term": meta["term"],
        },
        "units": list(units),
        "count": count,
        "difficulty": difficulty,
        "include_answers": include_answers,
        "grade": meta.get("grade") or "一年级",
    }
    if source_text is not None:
        state["source_text"] = source_text
    if generator is not None:
        state["generator"] = generator
    out = build_graph().invoke(state)
    if out.get("error"):
        raise TextbookError(str(out["error"]), int(out.get("error_status") or 400))
    questions = out.get("questions")
    if not isinstance(questions, list):
        raise TextbookError("题目数量与设置不一致，请重试。", 502)
    return questions
