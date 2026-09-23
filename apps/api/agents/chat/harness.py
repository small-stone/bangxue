"""DeepAgents chat harness for dialogue quiz (Mode B)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from deepagents import (
    FilesystemMiddleware,
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    create_deep_agent,
    register_harness_profile,
)
from deepagents.backends import StateBackend
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from openai import OpenAI

from agents.shared.bailian import (
    BailianConfigError,
    bailian_base_url,
    build_chat_model,
    quiz_model_name,
    require_bailian_api_key,
)
from agents.shared.checkpointer import get_checkpointer
from agents.shared.jev import CompletenessResult, JevConfigError, judge_chat_completeness
from app.question_format import normalize_options

_HOST_TOOLS = frozenset(
    {
        "execute",
        "task",
        "write_file",
        "edit_file",
        "delete",
        "ls",
        "glob",
        "grep",
    }
)

_PROFILE_REGISTERED = False

# thread_id -> session payload (draft lives here; checkpointer holds agent turns)
_SESSIONS: dict[str, dict[str, Any]] = {}


class ChatError(Exception):
    """User-facing chat failure."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class ChatTurnResult:
    status: str
    assistant_text: str
    questions: list[dict] = field(default_factory=list)
    summary: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


def _ensure_harness_profile() -> None:
    global _PROFILE_REGISTERED
    if _PROFILE_REGISTERED:
        return
    register_harness_profile(
        "openai",
        HarnessProfile(
            excluded_tools=_HOST_TOOLS,
            general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
        ),
    )
    _PROFILE_REGISTERED = True


def list_agent_tool_names(agent: Any) -> list[str]:
    tools_node = agent.nodes.get("tools")
    bound = getattr(tools_node, "bound", None)
    by_name = getattr(bound, "tools_by_name", None) or {}
    return sorted(by_name.keys())


def build_agent(*, checkpointer: Any | None = None):
    """Return a DeepAgents harness with draft_quiz only (no host shell execute)."""
    _ensure_harness_profile()
    backend = StateBackend()
    model = build_chat_model()

    @tool
    def draft_quiz(intent: str, count: int = 10, difficulty: str = "适中") -> str:
        """Draft printable quiz questions from the parent's stated intent."""
        questions = generate_chat_questions(
            intent=intent,
            count=count,
            difficulty=difficulty,
        )
        return json.dumps({"questions": questions}, ensure_ascii=False)

    agent = create_deep_agent(
        model=model,
        tools=[draft_quiz],
        system_prompt=(
            "你是帮学的对话出题助手，面向家长用中文交流。"
            "当家长意图已经足够时，调用 draft_quiz 生成题目；"
            "不要使用文件系统或执行命令；不要编造未调用工具得到的题目列表。"
        ),
        backend=backend,
        middleware=[FilesystemMiddleware(backend=backend, tools=["read_file"])],
        checkpointer=checkpointer if checkpointer is not None else get_checkpointer(),
        name="bangxue-chat",
    )
    names = list_agent_tool_names(agent)
    if "execute" in names:
        raise ChatError("对话 Agent 仍暴露宿主机 execute 工具，已拒绝启动。", 500)
    return agent


def create_session() -> str:
    """Create a chat thread and seed the Postgres checkpointer."""
    from langgraph.checkpoint.base import empty_checkpoint

    thread_id = uuid4().hex
    checkpointer = get_checkpointer()
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
    checkpointer.put(
        config,
        empty_checkpoint(),
        {"source": "input", "step": -1, "writes": {}, "parents": {}},
        {},
    )
    _SESSIONS[thread_id] = {
        "messages": [],
        "draft": None,
        "summary": "",
        "meta": {},
    }
    return thread_id


def session_exists(thread_id: str) -> bool:
    if thread_id in _SESSIONS:
        return True
    checkpointer = get_checkpointer()
    config = {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}
    return checkpointer.get_tuple(config) is not None


def get_session(thread_id: str) -> dict[str, Any]:
    if thread_id not in _SESSIONS:
        if not session_exists(thread_id):
            raise ChatError("对话会话不存在或已失效。", 404)
        _SESSIONS[thread_id] = {
            "messages": [],
            "draft": None,
            "summary": "",
            "meta": {},
        }
    return _SESSIONS[thread_id]


def handle_parent_message(thread_id: str, text: str) -> ChatTurnResult:
    """Jev gate then clarify or draft. Invokes DeepAgents when drafting."""
    text = (text or "").strip()
    if not text:
        raise ChatError("请先输入出题需求。")

    session = get_session(thread_id)
    session["messages"].append({"role": "user", "content": text})
    transcript = "\n".join(m["content"] for m in session["messages"] if m["role"] == "user")

    try:
        judgment = judge_chat_completeness(transcript)
    except JevConfigError as exc:
        raise ChatError(str(exc), 503) from exc

    if not judgment.enough or judgment.confidence < 0.6:
        reply = judgment.follow_up or "请再补充题量和具体知识点。"
        session["messages"].append({"role": "assistant", "content": reply})
        session["draft"] = None
        return ChatTurnResult(
            status="clarifying",
            assistant_text=reply,
            summary=judgment.summary,
            meta=_meta_from_judgment(judgment),
        )

    try:
        require_bailian_api_key()
    except BailianConfigError as exc:
        raise ChatError(str(exc), 503) from exc

    count = judgment.count or _default_count(transcript)
    if count > 100:
        reply = "题量最多 100 道，请改到 1–100 之间再告诉我。"
        session["messages"].append({"role": "assistant", "content": reply})
        session["draft"] = None
        return ChatTurnResult(
            status="clarifying",
            assistant_text=reply,
            summary=judgment.summary,
            meta=_meta_from_judgment(judgment),
        )
    if count < 1:
        reply = "请告诉我要出几道题（1–100 道）。"
        session["messages"].append({"role": "assistant", "content": reply})
        session["draft"] = None
        return ChatTurnResult(
            status="clarifying",
            assistant_text=reply,
            summary=judgment.summary,
            meta=_meta_from_judgment(judgment),
        )

    try:
        questions = _draft_via_agent(thread_id, transcript, count)
    except BailianConfigError as exc:
        raise ChatError(str(exc), 503) from exc
    except ChatError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ChatError(f"暂时无法出题：{exc}", 503) from exc

    if not questions:
        raise ChatError("模型没有返回题目列表。", 502)

    reply = f"已根据你的需求起草 {len(questions)} 道题，请确认后生成练习卷。"
    session["messages"].append({"role": "assistant", "content": reply})
    session["draft"] = {
        "questions": questions,
        "include_answers": True,
        "count": len(questions),
        "difficulty": "适中",
    }
    session["summary"] = judgment.summary
    session["meta"] = _meta_from_judgment(judgment)
    return ChatTurnResult(
        status="draft_ready",
        assistant_text=reply,
        questions=questions,
        summary=judgment.summary,
        meta=session["meta"],
    )


def confirm_session(thread_id: str) -> dict[str, Any]:
    """Persist draft into the shared quiz store and return quiz payload fields."""
    from app.quiz_store import save_quiz

    session = get_session(thread_id)
    draft = session.get("draft")
    if not draft or not draft.get("questions"):
        raise ChatError("还没有可确认的题目，请先补充出题需求。")

    questions = draft["questions"]
    summary = session.get("summary") or "对话出题"
    title = f"对话练习 · {summary[:40]}"
    quiz_id = save_quiz(
        {
            "title": title,
            "questions": questions,
            "include_answers": bool(draft.get("include_answers", True)),
            "meta": {
                "source": "chat",
                "summary": summary,
                "count": len(questions),
                "difficulty": draft.get("difficulty", "适中"),
                **(session.get("meta") or {}),
            },
        }
    )
    return {
        "id": quiz_id,
        "title": title,
        "questions": questions,
        "include_answers": bool(draft.get("include_answers", True)),
        "count": len(questions),
        "difficulty": draft.get("difficulty", "适中"),
        "source": "chat",
        "summary": summary,
    }


def generate_chat_questions(
    *,
    intent: str,
    count: int,
    difficulty: str = "适中",
    grade: str | None = None,
    subject: str | None = None,
) -> list[dict]:
    if not isinstance(count, int) or count < 1 or count > 100:
        raise ChatError("题量须为 1 至 100 道。", 400)

    api_key = require_bailian_api_key()
    model = quiz_model_name()
    client = OpenAI(api_key=api_key, base_url=bailian_base_url())
    grade_bit = grade or "小学"
    subject_bit = subject or "综合"
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        extra_body={"enable_thinking": False},
        messages=[
            {
                "role": "system",
                "content": (
                    f"你是{grade_bit}{subject_bit}出题助手。根据家长意图出题，不要超出所述范围。"
                    "返回 JSON：{\"questions\":[{\"qtype\":\"选择题|填空题|计算题\",\"stem\":\"...\","
                    "\"options\":[\"A. …\",\"B. …\",\"C. …\",\"D. …\"],\"answer\":\"...\"}]}。"
                    "选择题 MUST 提供 options（至少 4 个 A-D 选项）；填空题和计算题不要 options。"
                    f"题目数量必须正好是 {count}。难度：{difficulty}。"
                    "只返回题目 JSON，不要输出思考过程。"
                ),
            },
            {"role": "user", "content": intent},
        ],
    )
    payload = json.loads(response.choices[0].message.content or "{}")
    questions = payload.get("questions")
    if not isinstance(questions, list):
        raise ChatError("模型没有返回题目列表。", 502)
    cleaned: list[dict] = []
    for item in questions:
        stem = str(item.get("stem", "")).strip()
        if not stem:
            continue
        qtype = str(item.get("qtype") or "计算题").strip() or "计算题"
        row: dict = {
            "qtype": qtype,
            "stem": stem,
            "answer": str(item.get("answer", "")).strip(),
        }
        options = normalize_options(item.get("options"))
        if qtype == "选择题":
            if not options or len(options) < 2:
                raise ChatError("选择题缺少选项，请重试。", 502)
            row["options"] = options
        elif options:
            row["options"] = options
        cleaned.append(row)
    if len(cleaned) != count:
        raise ChatError("题目数量与设置不一致，请重试。", 502)
    return cleaned


def _draft_via_agent(thread_id: str, intent: str, count: int) -> list[dict]:
    """Prefer DeepAgents invoke; fall back to direct generation if tool result missing."""
    checkpointer = get_checkpointer()
    agent = build_agent(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}
    prompt = (
        f"家长需求如下，请调用 draft_quiz 生成题目。\n"
        f"intent: {intent}\n"
        f"count: {count}\n"
        f"difficulty: 适中"
    )
    result = agent.invoke(
        {"messages": [HumanMessage(content=prompt)]},
        config=config,
    )
    questions = _questions_from_agent_result(result)
    if questions:
        return questions
    return generate_chat_questions(intent=intent, count=count)


def _questions_from_agent_result(result: dict[str, Any]) -> list[dict]:
    messages = result.get("messages") or []
    for message in reversed(messages):
        content = getattr(message, "content", None)
        if not isinstance(content, str):
            continue
        if "questions" not in content:
            continue
        try:
            # Tool messages often are raw JSON; AI may wrap it.
            match = re.search(r"\{.*\"questions\".*\}", content, re.DOTALL)
            raw = match.group(0) if match else content
            payload = json.loads(raw)
            questions = payload.get("questions")
            if isinstance(questions, list) and questions:
                return questions
        except json.JSONDecodeError:
            continue
    return []


def _meta_from_judgment(judgment: CompletenessResult) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    if judgment.grade:
        meta["grade"] = judgment.grade
    if judgment.subject:
        meta["subject"] = judgment.subject
    return meta


def _default_count(text: str) -> int:
    match = re.search(r"(\d+)\s*[道题]", text)
    if match:
        value = int(match.group(1))
        if 1 <= value <= 100:
            return value
    return 10
