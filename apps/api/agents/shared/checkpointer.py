"""Postgres LangGraph checkpointer for chat threads (no MemorySaver default)."""

from __future__ import annotations

import os
from functools import lru_cache

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

_DEFAULT_URL = "postgresql://bangxue:bangxue@127.0.0.1:5432/bangxue"

_pool: ConnectionPool | None = None


class CheckpointerConfigError(RuntimeError):
    """Checkpointer cannot start without a Postgres database."""


def database_url() -> str:
    return os.environ.get("DATABASE_URL") or _DEFAULT_URL


@lru_cache(maxsize=1)
def get_checkpointer() -> PostgresSaver:
    """Return a process-wide Postgres checkpointer.

    Raises if Postgres is unreachable. Never falls back to an in-memory saver.
    """
    global _pool
    try:
        _pool = ConnectionPool(
            conninfo=database_url(),
            kwargs={"autocommit": True, "prepare_threshold": 0},
            open=True,
            min_size=1,
            max_size=5,
            timeout=10,
        )
        saver = PostgresSaver(_pool)
        saver.setup()
        return saver
    except Exception as exc:  # noqa: BLE001 - surface as config error
        raise CheckpointerConfigError(
            f"对话会话需要 Postgres Checkpointer，无法连接数据库：{exc}"
        ) from exc


def reset_checkpointer_cache() -> None:
    global _pool
    get_checkpointer.cache_clear()
    if _pool is not None:
        _pool.close()
        _pool = None
