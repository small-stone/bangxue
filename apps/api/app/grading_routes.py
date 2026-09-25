"""Photo upload, grading, score list, and wrong-question APIs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from agents.shared.grading import GradeResult, grade_questions
from app.quiz_store import get_quiz
from app.score_store import (
    DATA_DIR,
    confirm_attempt,
    create_attempt,
    get_attempt,
    list_confirmed_scores,
    list_wrong_questions,
    save_upload,
)

router = APIRouter(tags=["grading"])

ParentEmail = Annotated[str | None, Header(alias="X-Parent-Email")]


def _normalize_email(header: str | None) -> str | None:
    if not header:
        return None
    email = header.strip().lower()
    if "@" not in email:
        return None
    return email


def _attempt_public(row: dict) -> dict:
    return {
        "id": row["id"],
        "confirmed": bool(row.get("confirmed")),
        "demo": bool(row.get("demo")),
        "quiz_id": row.get("quiz_id"),
        "source": row.get("source"),
        "subject": row.get("subject"),
        "title": row.get("title"),
        "correct": row.get("correct"),
        "total": row.get("total"),
        "items": row.get("items") or [],
        "created_at": row.get("created_at"),
        "confirmed_at": row.get("confirmed_at"),
        "email": row.get("email"),
    }


def _resolve_questions(
    quiz_id: str | None,
    questions_json: str | None,
) -> tuple[list[dict], dict]:
    """Return (questions, meta) from live quiz or client snapshot."""
    meta: dict = {"title": "练习", "subject": "数学", "source": "textbook"}
    quiz = get_quiz(quiz_id) if quiz_id else None
    if quiz is not None:
        questions = quiz.get("questions") or []
        q_meta = quiz.get("meta") or {}
        meta["title"] = quiz.get("title") or meta["title"]
        meta["subject"] = q_meta.get("subject") or meta["subject"]
        return questions, meta

    if questions_json:
        try:
            raw = json.loads(questions_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="题目快照无效。") from exc
        if isinstance(raw, dict):
            questions = raw.get("questions") or []
            meta["title"] = raw.get("title") or meta["title"]
            meta["subject"] = raw.get("subject") or meta["subject"]
            meta["source"] = raw.get("source") or meta["source"]
        elif isinstance(raw, list):
            questions = raw
        else:
            raise HTTPException(status_code=400, detail="题目快照无效。")
        if not questions:
            raise HTTPException(status_code=400, detail="题目快照为空。")
        return questions, meta

    raise HTTPException(status_code=404, detail="练习已失效，请重新出题后再上传。")


@router.post("/grading/attempts")
async def create_grading_attempt(
    photos: Annotated[list[UploadFile], File()],
    quiz_id: Annotated[str | None, Form()] = None,
    questions_json: Annotated[str | None, Form()] = None,
    source: Annotated[str | None, Form()] = None,
    subject: Annotated[str | None, Form()] = None,
    title: Annotated[str | None, Form()] = None,
) -> dict:
    if not photos:
        raise HTTPException(status_code=400, detail="请先拍摄或选择答卷照片。")

    questions, meta = _resolve_questions(quiz_id, questions_json)
    if source in {"textbook", "chat"}:
        meta["source"] = source
    if subject:
        meta["subject"] = subject
    if title:
        meta["title"] = title

    photo_paths: list[str] = []
    abs_paths: list[Path] = []
    for photo in photos:
        content = await photo.read()
        if not content:
            continue
        rel = save_upload(photo.filename or "photo.jpg", content)
        photo_paths.append(rel)
        abs_paths.append(DATA_DIR / rel)

    if not photo_paths:
        raise HTTPException(status_code=400, detail="请先拍摄或选择答卷照片。")

    try:
        result: GradeResult = grade_questions(
            questions=questions,
            image_paths=abs_paths,
            quiz_id=quiz_id or "snapshot",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"判分失败：{exc}") from exc

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
    record = create_attempt(
        {
            "demo": result.demo,
            "quiz_id": quiz_id,
            "source": meta["source"],
            "subject": meta["subject"],
            "title": meta["title"],
            "correct": result.correct_count,
            "total": result.total,
            "items": items,
            "photo_paths": photo_paths,
        }
    )
    return _attempt_public(record)


@router.get("/grading/attempts/{attempt_id}")
def read_grading_attempt(attempt_id: str) -> dict:
    row = get_attempt(attempt_id)
    if row is None:
        raise HTTPException(status_code=404, detail="判分结果不存在或已失效。")
    return _attempt_public(row)


@router.post("/grading/attempts/{attempt_id}/confirm")
def confirm_grading_attempt(
    attempt_id: str,
    x_parent_email: ParentEmail = None,
) -> dict:
    email = _normalize_email(x_parent_email)
    if not email:
        raise HTTPException(status_code=401, detail="请先登录后再保存成绩。")
    row = get_attempt(attempt_id)
    if row is None:
        raise HTTPException(status_code=404, detail="判分结果不存在或已失效。")
    try:
        confirmed = confirm_attempt(attempt_id, email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="邮箱无效。") from exc
    if confirmed is None:
        raise HTTPException(status_code=404, detail="判分结果不存在或已失效。")
    return _attempt_public(confirmed)


@router.get("/scores")
def scores_list(x_parent_email: ParentEmail = None) -> dict:
    email = _normalize_email(x_parent_email)
    if not email:
        return {"scores": [], "guest": True}
    rows = list_confirmed_scores(email)
    return {"scores": [_attempt_public(r) for r in rows], "guest": False}


@router.get("/wrong-questions")
def wrong_questions_list(x_parent_email: ParentEmail = None) -> dict:
    email = _normalize_email(x_parent_email)
    if not email:
        return {"items": [], "guest": True}
    return {"items": list_wrong_questions(email), "guest": False}
