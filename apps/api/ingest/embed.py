"""Embedding backends selected by environment variables."""

import os
from collections.abc import Sequence


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Embed texts using EMBEDDING_PROVIDER (local or openai)."""
    provider = os.environ.get("EMBEDDING_PROVIDER", "local").strip().lower()
    if provider == "openai":
        return _embed_openai(texts)
    if provider == "local":
        return _embed_local(texts)
    raise RuntimeError(
        f"Unsupported EMBEDDING_PROVIDER={provider!r}. Use 'local' or 'openai'."
    )


def embedding_dimension() -> int:
    provider = os.environ.get("EMBEDDING_PROVIDER", "local").strip().lower()
    if provider == "openai":
        # text-embedding-3-small default width.
        return int(os.environ.get("EMBEDDING_DIMENSION", "1536"))
    return int(os.environ.get("EMBEDDING_DIMENSION", "512"))


def _embed_local(texts: Sequence[str]) -> list[list[float]]:
    from fastembed import TextEmbedding

    model_name = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
    model = TextEmbedding(model_name)
    return [list(map(float, vector)) for vector in model.embed(list(texts))]


def _embed_openai(texts: Sequence[str]) -> list[list[float]]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai.")
    from openai import OpenAI

    model_name = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(model=model_name, input=list(texts))
    ordered = sorted(response.data, key=lambda item: item.index)
    return [list(item.embedding) for item in ordered]
