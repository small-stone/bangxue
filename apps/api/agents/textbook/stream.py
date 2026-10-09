"""Reusable textbook quiz pipeline that yields status / question / result events."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from typing import Any

from agents.textbook.generate import (
    TextbookError,
    _bailian_generator,
    iter_bailian_raw_questions,
    load_unit_text,
)
from agents.textbook.graph import MAX_GENERATE_ATTEMPTS, _clean_generated_questions

Generator = Callable[..., list[dict]]


def iter_textbook_quiz_events(
    *,
    units: Sequence[str],
    count: int,
    difficulty: str,
    include_answers: bool,
    generator: Generator | None = None,
    source_text: str | None = None,
    **meta: str,
) -> Iterator[dict[str, Any]]:
    """Yield pipeline events for one textbook quiz request.

    Event shapes (``type`` field):
    - ``status``: phase progress (load_units / generating / validating)
    - ``question``: one cleaned question after full-set validation (best-effort UX)
    - ``result``: full cleaned question list (caller saves and emits ``done``)
    - ``error``: terminal failure (``detail``, optional ``status_code``)
    """
    total = count
    yield {
        "type": "status",
        "phase": "load_units",
        "message": "正在读取所选单元课文…",
        "total": total,
    }

    text = (source_text or "").strip()
    if not text:
        try:
            text = load_unit_text(units, **meta)
        except TextbookError as exc:
            yield {
                "type": "error",
                "detail": str(exc),
                "status_code": exc.status_code,
            }
            return

    if count not in {10, 15, 20, 30}:
        yield {
            "type": "error",
            "detail": "题量只能是 10、15、20 或 30。",
            "status_code": 400,
        }
        return
    if not text.strip():
        yield {
            "type": "error",
            "detail": "所选单元没有可用课文。",
            "status_code": 404,
        }
        return

    grade = meta.get("grade") or "一年级"
    subject = meta.get("subject") or "数学"
    last_error = "暂时无法出题，请重试。"
    last_status = 502
    use_default = generator is None

    for attempt in range(MAX_GENERATE_ATTEMPTS):
        if attempt > 0:
            yield {
                "type": "status",
                "phase": "generating",
                "message": f"出题未通过校验，正在重试（第 {attempt + 1} 次）…",
                "total": total,
            }
        else:
            yield {
                "type": "status",
                "phase": "generating",
                "message": "正在调用大模型出题…",
                "total": total,
            }

        raw: list | None = None
        try:
            if use_default:
                for ev in iter_bailian_raw_questions(
                    source_text=text,
                    count=count,
                    difficulty=difficulty,
                    include_answers=include_answers,
                    grade=grade,
                    subject=subject,
                ):
                    if ev["type"] == "status":
                        yield ev
                    elif ev["type"] == "raw_questions":
                        raw = ev["questions"]
            else:
                assert generator is not None
                raw = generator(
                    source_text=text,
                    count=count,
                    difficulty=difficulty,
                    include_answers=include_answers,
                    grade=grade,
                    subject=subject,
                )
        except TextbookError as exc:
            if exc.status_code < 500:
                yield {
                    "type": "error",
                    "detail": str(exc),
                    "status_code": exc.status_code,
                }
                return
            last_error, last_status = str(exc), exc.status_code
            continue
        except Exception as exc:  # noqa: BLE001
            last_error, last_status = f"暂时无法出题：{exc}", 503
            continue

        if not isinstance(raw, list):
            last_error, last_status = "模型没有返回题目列表。", 502
            continue

        yield {
            "type": "status",
            "phase": "validating",
            "message": "正在整理并校验题目…",
            "total": total,
        }
        cleaned, err, status = _clean_generated_questions(
            raw, count=count, include_answers=include_answers
        )
        if cleaned is not None:
            # Emit per-question only after full-set validation so completion stays reliable.
            for index, question in enumerate(cleaned):
                yield {
                    "type": "question",
                    "index": index,
                    "question": question,
                    "done": index + 1,
                    "total": total,
                }
            yield {"type": "result", "questions": cleaned}
            return
        last_error = err or last_error
        last_status = status or last_status

    yield {
        "type": "error",
        "detail": last_error,
        "status_code": last_status,
    }


def collect_textbook_questions(
    *,
    units: Sequence[str],
    count: int,
    difficulty: str,
    include_answers: bool,
    generator: Generator | None = None,
    source_text: str | None = None,
    **meta: str,
) -> list[dict]:
    """Run the streaming pipeline synchronously and return cleaned questions."""
    for event in iter_textbook_quiz_events(
        units=units,
        count=count,
        difficulty=difficulty,
        include_answers=include_answers,
        generator=generator,
        source_text=source_text,
        **meta,
    ):
        if event["type"] == "error":
            raise TextbookError(
                str(event["detail"]),
                int(event.get("status_code") or 400),
            )
        if event["type"] == "result":
            questions = event["questions"]
            if isinstance(questions, list):
                return questions
    raise TextbookError("暂时无法出题，请重试。", 502)


# Keep a sync alias used by graph-era call sites that inject generators.
default_generator = _bailian_generator
