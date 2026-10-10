"""LangChain Retrievers for textbook hybrid search (dense + sparse + Ensemble)."""

from __future__ import annotations

from typing import Any

import jieba
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict, Field, PrivateAttr
from rank_bm25 import BM25Okapi

from ingest.embed import embed_texts
from ingest.store import _vector_literal, connect

_CANDIDATE_LIMIT = 200
_DENSE_POOL = 24
_SPARSE_POOL = 24
_ENSEMBLE_C = 60


class RetrievalError(RuntimeError):
    """Configuration or infrastructure failure during retrieval."""


def load_scoped_candidates(
    *,
    stage: str,
    grade: str,
    subject: str,
    edition: str,
    term: str,
    limit: int = _CANDIDATE_LIMIT,
) -> list[dict[str, Any]]:
    """Load textbook rows for one book scope as plain dicts."""
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
                (stage, grade, subject, edition, term, limit),
            )
            rows = cur.fetchall()
    return [_row_to_meta(row) for row in rows]


def chunk_dict_to_document(row: dict[str, Any]) -> Document:
    return Document(
        page_content=str(row["content"]),
        metadata={
            "id": int(row["id"]),
            "unit_name": str(row["unit_name"]),
            "stage": str(row["stage"]),
            "grade": str(row["grade"]),
            "subject": str(row["subject"]),
            "edition": str(row["edition"]),
            "term": str(row["term"]),
        },
    )


def _row_to_meta(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "id": int(row[0]),
        "unit_name": str(row[1]),
        "content": str(row[2]),
        "stage": str(row[3]),
        "grade": str(row[4]),
        "subject": str(row[5]),
        "edition": str(row[6]),
        "term": str(row[7]),
    }


def _tokenize(text: str) -> list[str]:
    tokens = [t.strip() for t in jieba.lcut(text) if t.strip() and not t.isspace()]
    return tokens or [text]


class PgvectorTextbookRetriever(BaseRetriever):
    """Dense retriever over textbook_chunks with fixed book metadata scope."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    stage: str
    grade: str
    subject: str
    edition: str
    term: str
    k: int = _DENSE_POOL

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        del run_manager  # unused; required by BaseRetriever
        vectors = embed_texts([query])
        if not vectors or not vectors[0]:
            raise RetrievalError("查询向量为空。")
        literal = _vector_literal(vectors[0])
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
                    (
                        self.stage,
                        self.grade,
                        self.subject,
                        self.edition,
                        self.term,
                        literal,
                        self.k,
                    ),
                )
                rows = cur.fetchall()
        return [chunk_dict_to_document(_row_to_meta(row)) for row in rows]


class Bm25TextbookRetriever(BaseRetriever):
    """Sparse BM25 retriever over metadata-scoped candidates (jieba tokenization)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    stage: str
    grade: str
    subject: str
    edition: str
    term: str
    k: int = _SPARSE_POOL
    preloaded_candidates: list[dict[str, Any]] | None = Field(default=None, exclude=True)
    _candidates: list[dict[str, Any]] = PrivateAttr(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if self.preloaded_candidates is not None:
            self._candidates = list(self.preloaded_candidates)
        else:
            self._candidates = load_scoped_candidates(
                stage=self.stage,
                grade=self.grade,
                subject=self.subject,
                edition=self.edition,
                term=self.term,
            )

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        del run_manager
        if not self._candidates:
            return []
        corpus = [_tokenize(c["content"]) for c in self._candidates]
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(_tokenize(query))
        ranked = sorted(
            zip(self._candidates, scores, strict=True),
            key=lambda item: item[1],
            reverse=True,
        )
        positive = [row for row, score in ranked if score > 0]
        chosen = positive[: self.k] if positive else [row for row, _ in ranked[: self.k]]
        return [chunk_dict_to_document(row) for row in chosen]


def build_textbook_ensemble(
    *,
    stage: str,
    grade: str,
    subject: str,
    edition: str,
    term: str,
    dense_k: int = _DENSE_POOL,
    sparse_k: int = _SPARSE_POOL,
    candidates: list[dict[str, Any]] | None = None,
) -> EnsembleRetriever:
    """Build equal-weight EnsembleRetriever (RRF) over dense + sparse textbook paths."""
    dense = PgvectorTextbookRetriever(
        stage=stage,
        grade=grade,
        subject=subject,
        edition=edition,
        term=term,
        k=dense_k,
    )
    sparse = Bm25TextbookRetriever(
        stage=stage,
        grade=grade,
        subject=subject,
        edition=edition,
        term=term,
        k=sparse_k,
        preloaded_candidates=candidates,
    )
    return EnsembleRetriever(
        retrievers=[dense, sparse],
        weights=[0.5, 0.5],
        c=_ENSEMBLE_C,
        id_key="id",
    )
