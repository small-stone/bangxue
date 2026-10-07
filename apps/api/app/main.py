"""FastAPI application entrypoint."""

from bangxue_env import load_repo_env

load_repo_env()

import logging

from fastapi import FastAPI

from agents import chat, shared, textbook
from agents.chat.routes import router as chat_router
from app.grading_routes import router as grading_router
from app.routes import router
from app.quiz_store import QuizStoreError, bootstrap_quiz_store
from app.score_store import ScoreStoreError, bootstrap_score_store
from app.session_store import SessionStoreError, bootstrap_session_store

logger = logging.getLogger(__name__)

app = FastAPI(title="bangxue-api", version="0.0.1")
app.include_router(router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(grading_router, prefix="/api")

try:
    bootstrap_score_store()
except ScoreStoreError as exc:
    # Allow process to start for health/textbook; score routes fail closed at call time.
    logger.warning("Score store bootstrap skipped: %s", exc)

try:
    bootstrap_session_store()
except SessionStoreError as exc:
    logger.warning("Chat session store bootstrap skipped: %s", exc)

try:
    bootstrap_quiz_store()
except QuizStoreError as exc:
    logger.warning("Quiz paper store bootstrap skipped: %s", exc)


@app.get("/health")
def health() -> dict[str, str]:
    # Touch agent packages so import wiring stays verified.
    _ = (textbook.placeholder, chat.placeholder, shared.placeholder)
    return {"status": "ok"}
