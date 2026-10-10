"""Unit tests for optional Langfuse wiring (no network)."""

import agents.shared.bailian as bailian
import agents.shared.observability as observability


def test_langfuse_configured_requires_both_keys(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert observability.langfuse_configured() is False

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    assert observability.langfuse_configured() is False

    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    assert observability.langfuse_configured() is True

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "  ")
    assert observability.langfuse_configured() is False


def test_base_url_aliases_host(monkeypatch):
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://jp.cloud.langfuse.com")
    observability.ensure_langfuse_env_aliases()
    assert observability._strip_env("LANGFUSE_HOST") == "https://jp.cloud.langfuse.com"


def test_get_handler_none_without_keys(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert observability.get_langfuse_handler() is None


def test_observability_run_config_empty_without_keys(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert observability.observability_run_config(path="textbook") == {}


def test_observability_run_config_with_fake_handler(monkeypatch):
    class FakeHandler:
        pass

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk")
    monkeypatch.setattr(observability, "get_langfuse_handler", lambda: FakeHandler())
    cfg = observability.observability_run_config(
        path="chat",
        thread_id="t-1",
        metadata={"grade": "一年级"},
    )
    assert cfg["callbacks"]
    assert cfg["metadata"]["langfuse_session_id"] == "t-1"
    assert "chat" in cfg["metadata"]["langfuse_tags"]
    assert cfg["run_name"] == "chat-draft"


def test_observe_llm_call_yields_none_without_keys(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    with observability.observe_llm_call(path="textbook") as handler:
        assert handler is None


def test_build_chat_model_no_default_callbacks(monkeypatch):
    captured: dict = {}

    class FakeChat:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setenv("bailian_api_key", "test-key")
    monkeypatch.setattr(bailian, "ChatOpenAI", FakeChat)
    bailian.build_chat_model()
    assert "callbacks" not in captured


def test_flush_never_raises(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    observability.flush_observability()

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk")

    import langfuse as lf

    def boom(*_args, **_kwargs):
        raise RuntimeError("network")

    monkeypatch.setattr(lf, "get_client", boom)
    observability.flush_observability()
