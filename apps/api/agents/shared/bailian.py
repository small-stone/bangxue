"""Bailian (DashScope) chat model factory for in-process agents."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


class BailianConfigError(RuntimeError):
    """Missing or invalid Bailian configuration."""


def require_bailian_api_key() -> str:
    api_key = os.environ.get("bailian_api_key")
    if not api_key:
        raise BailianConfigError("暂时无法出题：未配置 bailian_api_key。")
    return api_key


def quiz_model_name() -> str:
    return os.environ.get("QUIZ_MODEL", "qwen3.7-plus")


def bailian_base_url() -> str:
    return os.environ.get(
        "BAILIAN_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


def build_chat_model(*, temperature: float = 0.2) -> ChatOpenAI:
    """Return a LangChain chat model pointed at Bailian's OpenAI-compatible API."""
    return ChatOpenAI(
        api_key=require_bailian_api_key(),
        base_url=bailian_base_url(),
        model=quiz_model_name(),
        temperature=temperature,
        # Bailian thinking tokens must not leak into tool/JSON content.
        extra_body={"enable_thinking": False},
    )
