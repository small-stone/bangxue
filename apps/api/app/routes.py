"""Textbook lookup and quiz routes."""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from agents.textbook.generate import TextbookError, list_units
from agents.textbook.graph import run_textbook_quiz
from agents.textbook.stream import iter_textbook_quiz_events
from app.pdf_paper import render_pdf
from app.quiz_store import QuizStoreError, get_quiz, save_quiz

router = APIRouter()


class QuizRequest(BaseModel):
    stage: str
    grade: str
    subject: str
    edition: str
    term: str
    units: list[str] = Field(min_length=1)
    count: int
    difficulty: str = "适中"
    include_answers: bool = False


@router.get("/textbooks/units")
def textbook_units(
    stage: str,
    grade: str,
    subject: str,
    edition: str,
    term: str,
) -> dict:
    try:
        names = list_units(
            stage=stage,
            grade=grade,
            subject=subject,
            edition=edition,
            term=term,
        )
    except TextbookError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return {"units": names}


def _quiz_title(body: QuizRequest, units: list[str]) -> str:
    return f"{body.grade}{body.subject} · {'、'.join(units)}练习"


def _persist_quiz(
    *,
    body: QuizRequest,
    units: list[str],
    count: int,
    difficulty: str,
    include_answers: bool,
    questions: list[dict],
) -> tuple[str, str]:
    title = _quiz_title(body, units)
    quiz_id = save_quiz(
        {
            "title": title,
            "questions": questions,
            "include_answers": include_answers,
            "meta": {
                "grade": body.grade,
                "subject": body.subject,
                "units": units,
                "count": count,
                "difficulty": difficulty,
            },
        }
    )
    return quiz_id, title


@router.post("/quizzes")
def create_quiz(body: QuizRequest) -> dict:
    meta = body.model_dump()
    units = meta.pop("units")
    count = meta.pop("count")
    difficulty = meta.pop("difficulty")
    include_answers = meta.pop("include_answers")
    try:
        questions = run_textbook_quiz(
            units=units,
            count=count,
            difficulty=difficulty,
            include_answers=include_answers,
            **meta,
        )
    except TextbookError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    try:
        quiz_id, title = _persist_quiz(
            body=body,
            units=units,
            count=count,
            difficulty=difficulty,
            include_answers=include_answers,
            questions=questions,
        )
    except QuizStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"id": quiz_id, "title": title, "questions": questions}


@router.post("/quizzes/stream")
def create_quiz_stream(body: QuizRequest) -> StreamingResponse:
    """SSE textbook quiz: status / question / done / error events."""
    meta = body.model_dump()
    units = meta.pop("units")
    count = meta.pop("count")
    difficulty = meta.pop("difficulty")
    include_answers = meta.pop("include_answers")

    def event_stream():
        try:
            for event in iter_textbook_quiz_events(
                units=units,
                count=count,
                difficulty=difficulty,
                include_answers=include_answers,
                **meta,
            ):
                kind = event.get("type")
                if kind == "status":
                    yield _sse(
                        {
                            "type": "status",
                            "phase": event.get("phase"),
                            "message": event.get("message"),
                            "done": event.get("done"),
                            "total": event.get("total", count),
                        }
                    )
                elif kind == "question":
                    yield _sse(
                        {
                            "type": "question",
                            "index": event.get("index"),
                            "question": event.get("question"),
                            "done": event.get("done"),
                            "total": event.get("total", count),
                        }
                    )
                elif kind == "result":
                    questions = event["questions"]
                    yield _sse(
                        {
                            "type": "status",
                            "phase": "saving",
                            "message": "正在保存练习卷…",
                            "total": count,
                        }
                    )
                    try:
                        quiz_id, title = _persist_quiz(
                            body=body,
                            units=units,
                            count=count,
                            difficulty=difficulty,
                            include_answers=include_answers,
                            questions=questions,
                        )
                    except QuizStoreError as exc:
                        yield _sse(
                            {
                                "type": "error",
                                "detail": str(exc),
                                "status_code": 503,
                            }
                        )
                        return
                    yield _sse(
                        {
                            "type": "done",
                            "id": quiz_id,
                            "title": title,
                            "questions": questions,
                        }
                    )
                elif kind == "error":
                    yield _sse(
                        {
                            "type": "error",
                            "detail": event.get("detail") or "暂时无法出题",
                            "status_code": event.get("status_code"),
                        }
                    )
        except Exception as exc:  # noqa: BLE001
            yield _sse(
                {
                    "type": "error",
                    "detail": f"暂时无法出题：{exc}",
                    "status_code": 503,
                }
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/quizzes/{quiz_id}/paper.pdf")
def paper_pdf(quiz_id: str) -> Response:
    return _pdf_response(quiz_id, answers=False)


@router.get("/quizzes/{quiz_id}/answers.pdf")
def answers_pdf(quiz_id: str) -> Response:
    return _pdf_response(quiz_id, answers=True)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _pdf_response(quiz_id: str, *, answers: bool) -> Response:
    try:
        quiz = get_quiz(quiz_id)
    except QuizStoreError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if quiz is None:
        raise HTTPException(status_code=404, detail="练习已失效，请重新出题。")
    if answers and not quiz["include_answers"]:
        raise HTTPException(status_code=404, detail="这次没有生成答案卷。")
    if answers:
        title = quiz["title"] + "（答案）"
        filename = "answers.pdf"
    else:
        title = quiz["title"]
        filename = "paper.pdf"
    payload = render_pdf(
        title=title,
        questions=quiz["questions"],
        include_answer=answers,
    )
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
