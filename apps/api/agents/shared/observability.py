"""Optional Langfuse observability (SDK v4, fail-open when unset or upload fails).

Follows Langfuse LangChain integration: env credentials + ``get_client()`` +
``CallbackHandler`` inside ``propagate_attributes`` for trace name / session / tags.
Docs: https://langfuse.com/docs/integrations/langchain/tracing
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger(__name__)

# Map short feature keys to descriptive Langfuse trace names (best practice).
_TRACE_NAMES = {
    "textbook": "textbook-quiz",
    "chat": "chat-draft",
    "supervisor": "supervisor-route",
    "grading": "vision-grade",
}


def _strip_env(name: str) -> str:
    return (os.environ.get(name) or "").strip().strip('"').strip("'")


def ensure_langfuse_env_aliases() -> None:
    """Prefer LANGFUSE_BASE_URL (docs); accept legacy LANGFUSE_HOST."""
    base = _strip_env("LANGFUSE_BASE_URL")
    host = _strip_env("LANGFUSE_HOST")
    if base and not host:
        os.environ["LANGFUSE_HOST"] = base
    elif host and not base:
        os.environ["LANGFUSE_BASE_URL"] = host


def langfuse_configured() -> bool:
    """True when both Langfuse keys are present (base URL optional)."""
    return bool(_strip_env("LANGFUSE_PUBLIC_KEY") and _strip_env("LANGFUSE_SECRET_KEY"))


def get_langfuse_handler():
    """Return a LangChain CallbackHandler, or None if disabled / init failed."""
    if not langfuse_configured():
        return None
    try:
        ensure_langfuse_env_aliases()
        from langfuse import get_client
        from langfuse.langchain import CallbackHandler

        # Initializes from LANGFUSE_PUBLIC_KEY / SECRET_KEY / BASE_URL.
        get_client()
        return CallbackHandler()
    except Exception:  # noqa: BLE001
        logger.exception("Langfuse handler init failed; continuing without tracing")
        return None


def observability_run_config(
    *,
    path: str,
    thread_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """LangChain RunnableConfig fragment with CallbackHandler when enabled.

    Prefer wrapping the call in ``observe_llm_call`` so ``propagate_attributes``
    sets trace_name / session_id / tags. This helper remains for simple cases.
    """
    handler = get_langfuse_handler()
    if handler is None:
        return {}
    meta: dict[str, Any] = {"feature": path}
    if metadata:
        meta.update(metadata)
    if thread_id:
        meta["langfuse_session_id"] = thread_id
    meta["langfuse_tags"] = list(
        dict.fromkeys([*(meta.get("langfuse_tags") or []), path, f"feature:{path}"])
    )
    return {
        "callbacks": [handler],
        "metadata": meta,
        "run_name": _TRACE_NAMES.get(path, path),
    }


@contextmanager
def observe_llm_call(
    *,
    path: str,
    session_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[Any | None]:
    """Yield a CallbackHandler under propagate_attributes, or None if disabled.

    Usage::

        with observe_llm_call(path="textbook", metadata={...}) as handler:
            cfg = {"callbacks": [handler]} if handler else {}
            model.with_config(cfg).stream(...)
    """
    if not langfuse_configured():
        yield None
        return

    ensure_langfuse_env_aliases()
    try:
        from langfuse import get_client, propagate_attributes
        from langfuse.langchain import CallbackHandler

        client = get_client()
        handler = CallbackHandler()
        tags = [path, f"feature:{path}"]
        meta = {"feature": path}
        if metadata:
            meta.update({k: str(v) for k, v in metadata.items() if v is not None})
        attrs: dict[str, Any] = {
            "trace_name": _TRACE_NAMES.get(path, path),
            "tags": tags,
            "metadata": meta,
        }
        if session_id:
            attrs["session_id"] = session_id
        with propagate_attributes(**attrs):
            yield handler
        try:
            client.flush()
        except Exception:  # noqa: BLE001
            logger.exception("Langfuse flush failed; ignoring")
    except Exception:  # noqa: BLE001
        logger.exception("Langfuse observe_llm_call failed; continuing without tracing")
        yield None


def flush_observability() -> None:
    """Best-effort flush; never raises to callers."""
    if not langfuse_configured():
        return
    try:
        ensure_langfuse_env_aliases()
        from langfuse import get_client

        client = get_client()
        if client is not None:
            client.flush()
    except Exception:  # noqa: BLE001
        logger.exception("Langfuse flush failed; ignoring")
