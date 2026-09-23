"""Persist textbook chunks in Postgres + pgvector."""

import os
from collections.abc import Callable, Sequence

import psycopg

from ingest.split import Chunk

Embedder = Callable[[Sequence[str]], list[list[float]]]

_TABLE = "textbook_chunks"


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set.")
    return url


def connect() -> psycopg.Connection:
    return psycopg.connect(database_url())


def ensure_schema(conn: psycopg.Connection, dimension: int) -> None:
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute(
            """
            SELECT format_type(a.atttypid, a.atttypmod)
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            WHERE c.relname = %s AND a.attname = 'embedding' AND a.attnum > 0
            """,
            (_TABLE,),
        )
        row = cur.fetchone()
        if row is None:
            cur.execute(
                f"""
                CREATE TABLE {_TABLE} (
                    id bigserial PRIMARY KEY,
                    stage text NOT NULL,
                    grade text NOT NULL,
                    subject text NOT NULL,
                    edition text NOT NULL,
                    term text NOT NULL,
                    unit_name text NOT NULL,
                    page_start integer NOT NULL,
                    page_end integer NOT NULL,
                    content text NOT NULL,
                    embedding vector({dimension}) NOT NULL
                )
                """
            )
            cur.execute(
                f"""
                CREATE INDEX textbook_chunks_meta_idx
                ON {_TABLE} (stage, grade, subject, edition, term, unit_name)
                """
            )
        elif row[0] != f"vector({dimension})":
            raise RuntimeError(
                f"Existing embedding column is {row[0]}, expected vector({dimension}). "
                "Drop textbook_chunks before changing embedding models."
            )
    conn.commit()


def replace_book(
    conn: psycopg.Connection,
    *,
    stage: str,
    grade: str,
    subject: str,
    edition: str,
    term: str,
    chunks: Sequence[Chunk],
    embedder: Embedder,
    dimension: int,
) -> int:
    """Delete existing rows for this book, then insert chunks. Returns inserted count."""
    vectors = embedder([chunk.content for chunk in chunks])
    if len(vectors) != len(chunks) or not vectors:
        raise RuntimeError("Embedder returned a different number of vectors than chunks.")
    actual = len(vectors[0])
    if actual != dimension:
        raise RuntimeError(
            f"Embedding length {actual} does not match configured dimension {dimension}."
        )
    ensure_schema(conn, actual)
    meta = (stage, grade, subject, edition, term)
    with conn.cursor() as cur:
        cur.execute(
            f"""
            DELETE FROM {_TABLE}
            WHERE stage = %s AND grade = %s AND subject = %s
              AND edition = %s AND term = %s
            """,
            meta,
        )
        for chunk, vector in zip(chunks, vectors, strict=True):
            if len(vector) != actual:
                raise RuntimeError(
                    f"Embedding length {len(vector)} does not match dimension {actual}."
                )
            cur.execute(
                f"""
                INSERT INTO {_TABLE} (
                    stage, grade, subject, edition, term,
                    unit_name, page_start, page_end, content, embedding
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    *meta,
                    chunk.unit_name,
                    chunk.page_start,
                    chunk.page_end,
                    chunk.content,
                    _vector_literal(vector),
                ),
            )
    conn.commit()
    return len(chunks)


def count_book(
    conn: psycopg.Connection,
    *,
    stage: str,
    grade: str,
    subject: str,
    edition: str,
    term: str,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT count(*) FROM {_TABLE}
            WHERE stage = %s AND grade = %s AND subject = %s
              AND edition = %s AND term = %s
            """,
            (stage, grade, subject, edition, term),
        )
        return int(cur.fetchone()[0])


def fetch_unit(
    conn: psycopg.Connection,
    *,
    stage: str,
    grade: str,
    subject: str,
    edition: str,
    term: str,
    unit_name: str,
) -> list[tuple[str, int, int, str]]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT unit_name, page_start, page_end, content
            FROM {_TABLE}
            WHERE stage = %s AND grade = %s AND subject = %s
              AND edition = %s AND term = %s AND unit_name = %s
            ORDER BY page_start, id
            """,
            (stage, grade, subject, edition, term, unit_name),
        )
        return list(cur.fetchall())


def _vector_literal(vector: Sequence[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"
