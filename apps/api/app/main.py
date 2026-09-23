"""FastAPI application entrypoint."""

from bangxue_env import load_repo_env

load_repo_env()

from fastapi import FastAPI

from agents import chat, shared, textbook
from app.routes import router

app = FastAPI(title="bangxue-api", version="0.0.1")
app.include_router(router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    # Touch agent packages so import wiring stays verified.
    _ = (textbook.placeholder, chat.placeholder, shared.placeholder)
    return {"status": "ok"}
