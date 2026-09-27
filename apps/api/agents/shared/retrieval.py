"""Hybrid textbook retrieval: metadata filter + BM25 + pgvector + RRF."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import jieba
from rank_bm25 import BM25Okapi

from ingest.embed import embed_texts
from ingest.store import _vector_literal, connect

_RRF_K = 60
_DEFAULT_TOP_K = 8
_CANDIDATE_LIMIT = 200
_DENSE_POOL = 24
_SPARSE_POOL = 24
_MAX_CONTEXT_CHARS = 8000


class RetrievalError(RuntimeError):
    """Configuration or infrastructure failure during retrieval."""


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
    """Return fused Top-K chunks for the book scope. Empty list = no hit."""
    q = (query or "").strip()
    if not q:
        return []
    if not all([stage, grade, subject, edition, term]):
        raise RetrievalError("检索需要学段、年级、科目、版本与学期。")

    try:
        candidates = _load_candidates(
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
        dense = _dense_rank(q, meta=(stage, grade, subject, edition, term), limit=_DENSE_POOL)
    except RuntimeError as exc:
        raise RetrievalError(str(exc)) from exc

    sparse = _bm25_rank(q, candidates, limit=_SPARSE_POOL)
    fused_ids = _rrf_fuse(
        [c.id for c in dense],
        [c.id for c in sparse],
        top_k=top_k,
    )
    by_id = {c.id: c for c in candidates}
    # Dense may include rows not in the BM25 candidate slice; re-fetch those if needed.
    for chunk in dense:
        by_id.setdefault(chunk.id, chunk)

    out: list[RetrievedChunk] = []
    for rank, chunk_id in enumerate(fused_ids):
        chunk = by_id.get(chunk_id)
        if chunk is None:
            continue
        out.append(
            RetrievedChunk(
                id=chunk.id,
                unit_name=chunk.unit_name,
                content=chunk.content,
                stage=chunk.stage,
                grade=chunk.grade,
                subject=chunk.subject,
                edition=chunk.edition,
                term=chunk.term,
                score=1.0 / (_RRF_K + rank + 1),
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


def _load_candidates(
    *,
    stage: str,
    grade: str,
    subject: str,
    edition: str,
    term: str,
) -> list[RetrievedChunk]:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, unit_name, content, stage, grade, subject, edition, term
                FROM textbook_chunks
                WHERE stage = %s AND grade = %s AND subject = %s
                  AND edition = %s AND term = %s
                ORDER BY page_start, id
                LIMIT %s
                """,
                (stage, grade, subject, edition, term, _CANDIDATE_LIMIT),
            )
            rows = cur.fetchall()
    return [
        RetrievedChunk(
            id=int(row[0]),
            unit_name=str(row[1]),
            content=str(row[2]),
            stage=str(row[3]),
            grade=str(row[4]),
            subject=str(row[5]),
            edition=str(row[6]),
            term=str(row[7]),
        )
        for row in rows
    ]


def _dense_rank(
    query: str,
    *,
    meta: tuple[str, str, str, str, str],
    limit: int,
) -> list[RetrievedChunk]:
    vectors = embed_texts([query])
    if not vectors or not vectors[0]:
        raise RetrievalError("查询向量为空。")
    literal = _vector_literal(vectors[0])
    stage, grade, subject, edition, term = meta
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, unit_name, content, stage, grade, subject, edition, term
                FROM textbook_chunks
                WHERE stage = %s AND grade = %s AND subject = %s
                  AND edition = %s AND term = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (stage, grade, subject, edition, term, literal, limit),
            )
            rows = cur.fetchall()
    return [
        RetrievedChunk(
            id=int(row[0]),
            unit_name=str(row[1]),
            content=str(row[2]),
            stage=str(row[3]),
            grade=str(row[4]),
            subject=str(row[5]),
            edition=str(row[6]),
            term=str(row[7]),
        )
        for row in rows
    ]


def _tokenize(text: str) -> list[str]:
    tokens = [t.strip() for t in jieba.lcut(text) if t.strip() and not t.isspace()]
    return tokens or [text]


def _bm25_rank(query: str, candidates: Sequence[RetrievedChunk], *, limit: int) -> list[RetrievedChunk]:
    if not candidates:
        return []
    corpus = [_tokenize(c.content) for c in candidates]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(zip(candidates, scores, strict=True), key=lambda item: item[1], reverse=True)
    # Keep positive scores first; if all zero, still return top by order for recall.
    positive = [chunk for chunk, score in ranked if score > 0]
    if positive:
        return positive[:limit]
    return [chunk for chunk, _ in ranked[:limit]]


def _rrf_fuse(dense_ids: Sequence[int], sparse_ids: Sequence[int], *, top_k: int) -> list[int]:
    scores: dict[int, float] = {}
    for rank, doc_id in enumerate(dense_ids):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (_RRF_K + rank + 1)
    for rank, doc_id in enumerate(sparse_ids):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (_RRF_K + rank + 1)
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [doc_id for doc_id, _ in ordered[:top_k]]


def format_chunks_for_debug(chunks: Sequence[RetrievedChunk]) -> list[dict[str, Any]]:
    return [
        {"id": c.id, "unit_name": c.unit_name, "score": round(c.score, 4), "chars": len(c.content)}
        for c in chunks
    ]
