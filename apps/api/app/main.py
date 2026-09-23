"""FastAPI application entrypoint."""

from fastapi import FastAPI

from agents import chat, shared, textbook

app = FastAPI(title="bangxue-api", version="0.0.1")


@app.get("/health")
def health() -> dict[str, str]:
    # Touch agent packages so import wiring stays verified.
    _ = (textbook.placeholder, chat.placeholder, shared.placeholder)
    return {"status": "ok"}
