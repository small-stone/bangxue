"""Embedding backends selected by environment variables."""

import os
from collections.abc import Sequence

_BAILIAN_BATCH = 20
_BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Embed texts using EMBEDDING_PROVIDER (bailian, local, or openai)."""
    provider = os.environ.get("EMBEDDING_PROVIDER", "local").strip().lower()
    if provider == "bailian":
        return _embed_bailian(texts)
    if provider == "openai":
        return _embed_openai(texts)
    if provider == "local":
        return _embed_local(texts)
    raise RuntimeError(
        f"Unsupported EMBEDDING_PROVIDER={provider!r}. Use 'bailian', 'local', or 'openai'."
    )


def embedding_dimension() -> int:
    provider = os.environ.get("EMBEDDING_PROVIDER", "local").strip().lower()
    if provider == "bailian":
        return int(os.environ.get("EMBEDDING_DIMENSION", "1024"))
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
    return _embed_batched(client, model_name, texts, dimensions=None)


def _embed_bailian(texts: Sequence[str]) -> list[list[float]]:
    api_key = os.environ.get("bailian_api_key")
    if not api_key:
        raise RuntimeError("bailian_api_key is required when EMBEDDING_PROVIDER=bailian.")
    from openai import OpenAI

    model_name = os.environ.get("EMBEDDING_MODEL", "qwen3.7-text-embedding")
    dimension = int(os.environ.get("EMBEDDING_DIMENSION", "1024"))
    client = OpenAI(
        api_key=api_key,
        base_url=os.environ.get("BAILIAN_BASE_URL", _BAILIAN_BASE_URL),
    )
    return _embed_batched(client, model_name, texts, dimensions=dimension)


def _embed_batched(client, model_name: str, texts: Sequence[str], dimensions: int | None) -> list[list[float]]:
    vectors: list[list[float]] = []
    items = list(texts)
    for start in range(0, len(items), _BAILIAN_BATCH):
        batch = items[start : start + _BAILIAN_BATCH]
        kwargs = {"model": model_name, "input": batch}
        if dimensions is not None:
            kwargs["dimensions"] = dimensions
        response = client.embeddings.create(**kwargs)
        ordered = sorted(response.data, key=lambda item: item.index)
        vectors.extend(list(item.embedding) for item in ordered)
    return vectors
