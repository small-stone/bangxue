"""Hybrid textbook retrieval facade: metadata scope + LangChain EnsembleRetriever."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from agents.shared.retrievers import (
    RetrievalError,
    build_textbook_ensemble,
    load_scoped_candidates,
)

_DEFAULT_TOP_K = 8
_ENSEMBLE_C = 60
_MAX_CONTEXT_CHARS = 8000

__all__ = [
    "RetrievalError",
    "RetrievedChunk",
    "format_chunks_for_debug",
    "hybrid_retrieve",
    "join_chunk_texts",
    "retrieval_summary",
]


@dataclass(frozen=True)
class RetrievedChunk:
    id: int
    unit_name: str
    content: str
    stage: str
    grade: str
    subject: str
    edition: str
    term: str
    score: float = 0.0


def hybrid_retrieve(
    query: str,
    *,
    stage: str,
    grade: str,
    subject: str,
    edition: str = "人教版",
    term: str = "上册",
    top_k: int = _DEFAULT_TOP_K,
) -> list[RetrievedChunk]:
    """Return fused Top-K chunks for the book scope via EnsembleRetriever."""
    q = (query or "").strip()
    if not q:
        return []
    if not all([stage, grade, subject, edition, term]):
        raise RetrievalError("检索需要学段、年级、科目、版本与学期。")

    try:
        candidates = load_scoped_candidates(
            stage=stage,
            grade=grade,
            subject=subject,
            edition=edition,
            term=term,
        )
    except RuntimeError as exc:
        raise RetrievalError(str(exc)) from exc

    if not candidates:
        return []

    try:
        ensemble = build_textbook_ensemble(
            stage=stage,
            grade=grade,
            subject=subject,
            edition=edition,
            term=term,
            candidates=candidates,
        )
        docs = ensemble.invoke(q)
    except RetrievalError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise RetrievalError(str(exc)) from exc

    out: list[RetrievedChunk] = []
    for rank, doc in enumerate(docs[:top_k]):
        meta = doc.metadata or {}
        try:
            chunk_id = int(meta["id"])
        except (KeyError, TypeError, ValueError):
            continue
        out.append(
            RetrievedChunk(
                id=chunk_id,
                unit_name=str(meta.get("unit_name") or ""),
                content=str(doc.page_content or ""),
                stage=str(meta.get("stage") or stage),
                grade=str(meta.get("grade") or grade),
                subject=str(meta.get("subject") or subject),
                edition=str(meta.get("edition") or edition),
                term=str(meta.get("term") or term),
                score=1.0 / (_ENSEMBLE_C + rank + 1),
            )
        )
    return out


def join_chunk_texts(chunks: Sequence[RetrievedChunk], *, max_chars: int = _MAX_CONTEXT_CHARS) -> str:
    parts: list[str] = []
    used = 0
    for chunk in chunks:
        piece = f"【{chunk.unit_name}】\n{chunk.content.strip()}"
        if not chunk.content.strip():
            continue
        if used and used + len(piece) > max_chars:
            break
        parts.append(piece)
        used += len(piece)
    return "\n\n".join(parts)


def retrieval_summary(
    chunks: Sequence[RetrievedChunk],
    *,
    stage: str,
    grade: str,
    subject: str,
    edition: str,
    term: str,
) -> str:
    units = []
    seen: set[str] = set()
    for chunk in chunks:
        if chunk.unit_name not in seen:
            seen.add(chunk.unit_name)
            units.append(chunk.unit_name)
    unit_bit = "、".join(units[:5]) if units else "无单元命中"
    return f"{stage}{grade}{subject}{edition}{term} · {unit_bit}"


def format_chunks_for_debug(chunks: Sequence[RetrievedChunk]) -> list[dict[str, Any]]:
    return [
        {"id": c.id, "unit_name": c.unit_name, "score": round(c.score, 4), "chars": len(c.content)}
        for c in chunks
    ]
