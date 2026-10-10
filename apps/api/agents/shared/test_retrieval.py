"""Unit tests for Ensemble-based textbook hybrid retrieval."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document

from agents.shared import build_textbook_ensemble, hybrid_retrieve
from agents.shared.retrieval import RetrievalError, join_chunk_texts, RetrievedChunk
from agents.shared.retrievers import Bm25TextbookRetriever


def _cand(chunk_id: int, *, grade: str = "一年级", content: str = "口算练习") -> dict:
    return {
        "id": chunk_id,
        "unit_name": f"单元{chunk_id}",
        "content": content,
        "stage": "小学",
        "grade": grade,
        "subject": "数学",
        "edition": "人教版",
        "term": "上册",
    }


def test_ensemble_import_and_factory_type():
    with patch(
        "agents.shared.retrievers.load_scoped_candidates",
        return_value=[_cand(1)],
    ):
        ensemble = build_textbook_ensemble(
            stage="小学",
            grade="一年级",
            subject="数学",
            edition="人教版",
            term="上册",
            candidates=[_cand(1), _cand(2)],
        )
    assert isinstance(ensemble, EnsembleRetriever)
    assert ensemble.id_key == "id"
    assert len(ensemble.retrievers) == 2


def test_hybrid_retrieve_requires_meta():
    with pytest.raises(RetrievalError, match="学段"):
        hybrid_retrieve("口算", stage="", grade="一年级", subject="数学")


def test_hybrid_retrieve_empty_query():
    assert hybrid_retrieve("  ", stage="小学", grade="一年级", subject="数学") == []


def test_hybrid_retrieve_empty_candidates():
    with patch(
        "agents.shared.retrieval.load_scoped_candidates",
        return_value=[],
    ):
        assert (
            hybrid_retrieve(
                "口算",
                stage="小学",
                grade="一年级",
                subject="数学",
                edition="人教版",
                term="上册",
            )
            == []
        )


def test_hybrid_retrieve_uses_ensemble_and_scopes_metadata():
    docs = [
        Document(
            page_content="口算一",
            metadata={
                "id": 11,
                "unit_name": "第一单元",
                "stage": "小学",
                "grade": "一年级",
                "subject": "数学",
                "edition": "人教版",
                "term": "上册",
            },
        ),
        Document(
            page_content="口算二",
            metadata={
                "id": 12,
                "unit_name": "第二单元",
                "stage": "小学",
                "grade": "一年级",
                "subject": "数学",
                "edition": "人教版",
                "term": "上册",
            },
        ),
    ]
    fake_ensemble = MagicMock(spec=EnsembleRetriever)
    fake_ensemble.invoke.return_value = docs

    with (
        patch(
            "agents.shared.retrieval.load_scoped_candidates",
            return_value=[_cand(11), _cand(12)],
        ),
        patch(
            "agents.shared.retrieval.build_textbook_ensemble",
            return_value=fake_ensemble,
        ) as build,
    ):
        chunks = hybrid_retrieve(
            "口算",
            stage="小学",
            grade="一年级",
            subject="数学",
            edition="人教版",
            term="上册",
            top_k=8,
        )

    build.assert_called_once()
    fake_ensemble.invoke.assert_called_once_with("口算")
    assert len(chunks) == 2
    assert {c.grade for c in chunks} == {"一年级"}
    assert {c.subject for c in chunks} == {"数学"}
    assert all(c.edition == "人教版" and c.term == "上册" for c in chunks)
    assert "二年级" not in {c.grade for c in chunks}


def test_bm25_empty_candidates_returns_empty():
    retriever = Bm25TextbookRetriever(
        stage="小学",
        grade="一年级",
        subject="数学",
        edition="人教版",
        term="上册",
        preloaded_candidates=[],
    )
    assert retriever.invoke("口算") == []


def test_bm25_results_stay_in_scope():
    retriever = Bm25TextbookRetriever(
        stage="小学",
        grade="一年级",
        subject="数学",
        edition="人教版",
        term="上册",
        preloaded_candidates=[
            _cand(1, content="一年级口算加减"),
            _cand(2, content="认识图形"),
        ],
    )
    docs = retriever.invoke("口算")
    assert docs
    assert all(d.metadata["grade"] == "一年级" for d in docs)
    assert all(d.metadata["subject"] == "数学" for d in docs)


def test_join_chunk_texts_unchanged():
    text = join_chunk_texts(
        [
            RetrievedChunk(
                id=1,
                unit_name="第一单元",
                content="正文A",
                stage="小学",
                grade="一年级",
                subject="数学",
                edition="人教版",
                term="上册",
            )
        ]
    )
    assert "【第一单元】" in text
    assert "正文A" in text
