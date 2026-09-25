"""FastAPI application entrypoint."""

from bangxue_env import load_repo_env

load_repo_env()

from fastapi import FastAPI

from agents import chat, shared, textbook
from agents.chat.routes import router as chat_router
from app.grading_routes import router as grading_router
from app.routes import router
from app.score_store import ensure_data_dirs

app = FastAPI(title="bangxue-api", version="0.0.1")
app.include_router(router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(grading_router, prefix="/api")
ensure_data_dirs()


@app.get("/health")
def health() -> dict[str, str]:
    # Touch agent packages so import wiring stays verified.
    _ = (textbook.placeholder, chat.placeholder, shared.placeholder)
    return {"status": "ok"}
