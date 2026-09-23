"""Dialogue quiz HTTP routes (Mode B)."""

from __future__ import annotations

import json
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agents.chat import ChatError, confirm_session, create_session, handle_parent_message, session_exists
from agents.shared.checkpointer import CheckpointerConfigError

router = APIRouter(prefix="/chat", tags=["chat"])

_TOKEN_CHUNK_SIZE = 2
_TOKEN_DELAY_SEC = 0.028


class MessageBody(BaseModel):
    text: str = Field(min_length=1)


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ChatError):
        return HTTPException(status_code=exc.status_code, detail=str(exc))
    if isinstance(exc, CheckpointerConfigError):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


@router.post("/sessions")
def open_session() -> dict:
    try:
        thread_id = create_session()
    except Exception as exc:  # noqa: BLE001
        raise _http_error(exc) from exc
    return {"thread_id": thread_id}


@router.post("/sessions/{thread_id}/messages")
def post_message(thread_id: str, body: MessageBody) -> StreamingResponse:
    if not session_exists(thread_id):
        raise HTTPException(status_code=404, detail="对话会话不存在或已失效。")

    def event_stream():
        try:
            yield _sse({"event": "progress", "message": "正在理解你的需求…"})
            result = handle_parent_message(thread_id, body.text)
            for piece in _chunk_text(result.assistant_text or ""):
                yield _sse({"event": "token", "text": piece})
                time.sleep(_TOKEN_DELAY_SEC)
            yield _sse(
                {
                    "event": "done",
                    "status": result.status,
                    "assistant_text": result.assistant_text,
                    "questions": result.questions,
                    "summary": result.summary,
                    "meta": result.meta,
                }
            )
        except Exception as exc:  # noqa: BLE001
            err = _http_error(exc)
            detail = str(err.detail)
            for piece in _chunk_text(detail):
                yield _sse({"event": "token", "text": piece})
                time.sleep(_TOKEN_DELAY_SEC)
            yield _sse(
                {
                    "event": "done",
                    "status": "error",
                    "assistant_text": detail,
                    "questions": [],
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


@router.post("/sessions/{thread_id}/confirm")
def confirm(thread_id: str) -> dict:
    try:
        return confirm_session(thread_id)
    except Exception as exc:  # noqa: BLE001
        raise _http_error(exc) from exc


def _chunk_text(text: str, size: int = _TOKEN_CHUNK_SIZE):
    if not text:
        return
    for index in range(0, len(text), size):
        yield text[index : index + size]


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
