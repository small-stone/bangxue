"""LangGraph StateGraph for shared answer-sheet grading."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from agents.shared.bailian import BailianConfigError
from agents.shared.grading import GradeItem, GradeResult, _demo_allowed, demo_grade, vision_grade


class GradingState(TypedDict):
    quiz_id: str
    questions: list[dict]
    image_paths: list[str]
    items: NotRequired[list[dict]]
    correct: NotRequired[int]
    total: NotRequired[int]
    demo: NotRequired[bool]
    error: NotRequired[str]


def _prepare_inputs(state: GradingState) -> dict[str, Any]:
    questions = state.get("questions") or []
    if not questions:
        return {"error": "题目快照为空。"}
    paths = state.get("image_paths") or []
    if not paths:
        return {"error": "请先拍摄或选择答卷照片。"}
    return {}


def _grade_vision_or_demo(state: GradingState) -> dict[str, Any]:
    if state.get("error"):
        return {}
    questions = state["questions"]
    quiz_id = state.get("quiz_id") or "snapshot"
    paths = [Path(p) for p in state.get("image_paths") or []]

    has_key = bool(os.environ.get("bailian_api_key"))
    if not has_key:
        if not _demo_allowed():
            return {"error": "暂时无法判分：未配置 bailian_api_key。"}
        result = demo_grade(questions, quiz_id)
    else:
        try:
            result = vision_grade(questions, paths)
        except Exception:
            if not _demo_allowed():
                raise
            result = demo_grade(questions, quiz_id)

    items = [
        {
            "index": item.index,
            "stem": item.stem,
            "correct": item.correct,
            "answer": item.answer,
            "student_answer": item.student_answer,
        }
        for item in result.items
    ]
    return {
        "items": items,
        "correct": result.correct_count,
        "total": result.total,
        "demo": result.demo,
    }


def _build_draft(state: GradingState) -> dict[str, Any]:
    # Draft fields already set by grade node; keep for explicit graph shape.
    if state.get("error"):
        return {}
    if "items" not in state:
        return {"error": "判分未产出结果。"}
    return {}


@lru_cache(maxsize=1)
def build_grading_graph():
    """Compile grading StateGraph (no checkpointer; one-shot invoke)."""
    graph = StateGraph(GradingState)
    graph.add_node("resolve_questions", _prepare_inputs)
    graph.add_node("grade_vision_or_demo", _grade_vision_or_demo)
    graph.add_node("build_draft", _build_draft)
    graph.add_edge(START, "resolve_questions")
    graph.add_edge("resolve_questions", "grade_vision_or_demo")
    graph.add_edge("grade_vision_or_demo", "build_draft")
    graph.add_edge("build_draft", END)
    return graph.compile()


def run_grading_graph(
    *,
    questions: list[dict],
    image_paths: list[Path],
    quiz_id: str,
) -> GradeResult:
    out = build_grading_graph().invoke(
        {
            "quiz_id": quiz_id,
            "questions": questions,
            "image_paths": [str(p) for p in image_paths],
        }
    )
    if out.get("error"):
        raise BailianConfigError(str(out["error"]))
    items_raw = out.get("items") or []
    items = [
        GradeItem(
            index=int(row["index"]),
            stem=str(row.get("stem") or ""),
            correct=bool(row.get("correct")),
            answer=row.get("answer"),
            student_answer=row.get("student_answer"),
        )
        for row in items_raw
    ]
    return GradeResult(items=items, demo=bool(out.get("demo")))
