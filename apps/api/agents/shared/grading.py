"""Answer-sheet grading: Bailian vision when configured, else deterministic demo."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents.shared.bailian import BailianConfigError, bailian_base_url, require_bailian_api_key

GRADING_TIMEOUT_SEC = 60


@dataclass
class GradeItem:
    index: int
    stem: str
    correct: bool
    answer: str | None = None
    student_answer: str | None = None


@dataclass
class GradeResult:
    items: list[GradeItem]
    demo: bool

    @property
    def correct_count(self) -> int:
        return sum(1 for item in self.items if item.correct)

    @property
    def total(self) -> int:
        return len(self.items)


def _vision_model() -> str:
    return os.environ.get("GRADING_VISION_MODEL", "qwen-vl-plus")


def _demo_allowed() -> bool:
    return os.environ.get("GRADING_DISABLE_DEMO", "").strip() not in {"1", "true", "yes"}


def demo_grade(questions: list[dict], quiz_id: str) -> GradeResult:
    """Deterministic fake grading so the UI path works without a vision key."""
    seed = int(hashlib.sha256((quiz_id or "demo").encode("utf-8")).hexdigest()[:8], 16)
    items: list[GradeItem] = []
    n = len(questions) or 1
    # Aim for roughly 80–95% correct based on seed.
    wrong_slots = {(seed + i * 7) % n for i in range(max(1, n // 10))}
    if n >= 4:
        wrong_slots.add((seed // 3) % n)
    for i, q in enumerate(questions):
        stem = str(q.get("stem") or f"第 {i + 1} 题")
        answer = q.get("answer")
        is_correct = i not in wrong_slots
        items.append(
            GradeItem(
                index=i + 1,
                stem=stem,
                correct=is_correct,
                answer=str(answer) if answer is not None else None,
                student_answer=None if is_correct else "（识别作答）",
            )
        )
    if not items:
        items.append(GradeItem(index=1, stem="（无题目）", correct=True))
    return GradeResult(items=items, demo=True)


def _image_data_url(path: Path) -> str:
    raw = path.read_bytes()
    suffix = path.suffix.lower().lstrip(".") or "jpeg"
    mime = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }.get(suffix, "image/jpeg")
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _parse_vision_json(text: str) -> list[dict]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    data = json.loads(text)
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    if not isinstance(data, list):
        raise ValueError("vision result is not a list")
    return data


def vision_grade(questions: list[dict], image_paths: list[Path]) -> GradeResult:
    from openai import OpenAI

    api_key = require_bailian_api_key()
    client = OpenAI(api_key=api_key, base_url=bailian_base_url(), timeout=GRADING_TIMEOUT_SEC)

    quiz_lines = []
    for i, q in enumerate(questions):
        ans = q.get("answer")
        quiz_lines.append(f"{i + 1}. {q.get('stem', '')}\n标准答案: {ans if ans is not None else '（无）'}")

    content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "你是答卷判分助手。根据图片中的学生作答，对照下列题目与标准答案，"
                "判断每题对错。只输出 JSON 数组，每项字段："
                'index(从1开始), correct(bool), student_answer(字符串可空)。\n\n'
                + "\n\n".join(quiz_lines)
            ),
        }
    ]
    for path in image_paths:
        content.append({"type": "image_url", "image_url": {"url": _image_data_url(path)}})

    response = client.chat.completions.create(
        model=_vision_model(),
        messages=[{"role": "user", "content": content}],
        temperature=0,
    )
    text = (response.choices[0].message.content or "").strip()
    parsed = _parse_vision_json(text)
    by_index = {int(row.get("index", 0)): row for row in parsed if isinstance(row, dict)}

    items: list[GradeItem] = []
    for i, q in enumerate(questions):
        row = by_index.get(i + 1) or {}
        items.append(
            GradeItem(
                index=i + 1,
                stem=str(q.get("stem") or f"第 {i + 1} 题"),
                correct=bool(row.get("correct", False)),
                answer=str(q["answer"]) if q.get("answer") is not None else None,
                student_answer=str(row["student_answer"]) if row.get("student_answer") else None,
            )
        )
    return GradeResult(items=items, demo=False)


def grade_questions(
    *,
    questions: list[dict],
    image_paths: list[Path],
    quiz_id: str,
) -> GradeResult:
    """Facade: run the shared grading LangGraph."""
    from agents.shared.grading_graph import run_grading_graph

    return run_grading_graph(
        questions=questions,
        image_paths=image_paths,
        quiz_id=quiz_id,
    )
