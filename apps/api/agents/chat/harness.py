"""DeepAgents chat harness for dialogue quiz (Mode B)."""

from __future__ import annotations

import json
import re
from contextvars import ContextVar
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
from agents.shared.retrieval import (
    RetrievalError,
    hybrid_retrieve,
    join_chunk_texts,
    retrieval_summary,
)
from app.question_format import normalize_options
from app.session_store import (
    SessionStoreError,
    empty_session,
    load_session,
    save_session,
    session_exists as store_session_exists,
)

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

# Distinct from Supervisor (`supervisor`) so shared thread_id does not collide.
CHAT_CHECKPOINT_NS = "chat-agent"

# Process-local cache only; PostgreSQL is authoritative (see session_store).
_SESSIONS: dict[str, dict[str, Any]] = {}

# Grounding context for draft_quiz tool within a single request.
_SOURCE_TEXT: ContextVar[str] = ContextVar("chat_source_text", default="")
_SOURCE_GRADE: ContextVar[str] = ContextVar("chat_source_grade", default="")
_SOURCE_SUBJECT: ContextVar[str] = ContextVar("chat_source_subject", default="")


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
        source_text = _SOURCE_TEXT.get()
        if not source_text.strip():
            raise ChatError("缺少教材检索上下文，无法出题。", 502)
        questions = generate_chat_questions(
            intent=intent,
            count=count,
            difficulty=difficulty,
            grade=_SOURCE_GRADE.get() or None,
            subject=_SOURCE_SUBJECT.get() or None,
            source_text=source_text,
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
    """Create a chat thread, persist session, and seed the Postgres checkpointer."""
    from langgraph.checkpoint.base import empty_checkpoint

    thread_id = uuid4().hex
    session = empty_session()
    try:
        save_session(thread_id, session)
    except SessionStoreError as exc:
        raise ChatError(str(exc), 503) from exc
    _SESSIONS[thread_id] = session

    checkpointer = get_checkpointer()
    config = {
        "configurable": {"thread_id": thread_id, "checkpoint_ns": CHAT_CHECKPOINT_NS}
    }
    checkpointer.put(
        config,
        empty_checkpoint(),
        {"source": "input", "step": -1, "writes": {}, "parents": {}},
        {},
    )
    return thread_id


def session_exists(thread_id: str) -> bool:
    if thread_id in _SESSIONS:
        return True
    try:
        return store_session_exists(thread_id)
    except SessionStoreError as exc:
        raise ChatError(str(exc), 503) from exc


def get_session(thread_id: str) -> dict[str, Any]:
    if thread_id in _SESSIONS:
        return _SESSIONS[thread_id]
    try:
        loaded = load_session(thread_id)
    except SessionStoreError as exc:
        raise ChatError(str(exc), 503) from exc
    if loaded is None:
        raise ChatError("对话会话不存在或已失效。", 404)
    _SESSIONS[thread_id] = loaded
    return loaded


def persist_session(thread_id: str) -> None:
    """Write cached session payload to the authoritative store."""
    session = _SESSIONS.get(thread_id)
    if session is None:
        return
    try:
        save_session(thread_id, session)
    except SessionStoreError as exc:
        raise ChatError(str(exc), 503) from exc


def handle_parent_message(thread_id: str, text: str) -> ChatTurnResult:
    """Route via in-process Supervisor, then clarify / chat draft / textbook quiz."""
    text = (text or "").strip()
    if not text:
        raise ChatError("请先输入出题需求。")

    session = get_session(thread_id)
    session["messages"].append({"role": "user", "content": text})
    persist_session(thread_id)
    transcript = "\n".join(m["content"] for m in session["messages"] if m["role"] == "user")

    from agents.supervisor import run_supervisor

    try:
        out = run_supervisor(thread_id, text, transcript=transcript)
    except ChatError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ChatError(f"暂时无法出题：{exc}", 503) from exc

    return ChatTurnResult(
        status=str(out.get("status") or "clarifying"),
        assistant_text=str(out.get("assistant_text") or ""),
        questions=list(out.get("questions") or []),
        summary=str(out.get("summary") or ""),
        meta=dict(out.get("meta") or {}),
    )


def apply_clarify(thread_id: str, decision) -> ChatTurnResult:
    """Supervisor clarify node: follow-up only, clear draft."""
    session = get_session(thread_id)
    reply = (getattr(decision, "follow_up", None) or "").strip() or (
        "请补充年级（或学段）、具体知识点和题量（1–100 道）。"
    )
    session["messages"].append({"role": "assistant", "content": reply})
    session["draft"] = None
    from agents.supervisor.route import decision_to_meta

    meta = decision_to_meta(decision)
    persist_session(thread_id)
    return ChatTurnResult(
        status="clarifying",
        assistant_text=reply,
        summary=getattr(decision, "summary", "") or "",
        meta=meta,
    )


def apply_chat_draft(thread_id: str, transcript: str, decision) -> ChatTurnResult:
    """Supervisor chat_draft node: hybrid retrieve + DeepAgents / grounded generate."""
    session = get_session(thread_id)
    try:
        require_bailian_api_key()
    except BailianConfigError as exc:
        raise ChatError(str(exc), 503) from exc

    from agents.supervisor.route import RouteDecision, decision_to_meta

    count = getattr(decision, "count", None) or _default_count(transcript)
    if count > 100:
        return apply_clarify(
            thread_id,
            RouteDecision(
                route="clarify",
                follow_up="题量最多 100 道，请改到 1–100 之间再告诉我。",
                summary=getattr(decision, "summary", ""),
                count=count,
                reason="count_out_of_range",
            ),
        )
    if count < 1:
        return apply_clarify(
            thread_id,
            RouteDecision(
                route="clarify",
                follow_up="请告诉我要出几道题（1–100 道）。",
                summary=getattr(decision, "summary", ""),
                reason="count_missing",
            ),
        )

    scope = {
        "stage": "小学",
        "grade": getattr(decision, "grade", "") or "",
        "subject": getattr(decision, "subject", "") or "数学",
        "edition": getattr(decision, "edition", "") or "人教版",
        "term": getattr(decision, "term", "") or "上册",
    }
    # Fall back to Jev completeness for grade if route omitted it.
    if not scope["grade"]:
        try:
            judgment = judge_chat_completeness(transcript)
            if judgment.grade:
                scope["grade"] = judgment.grade
            if judgment.subject:
                scope["subject"] = judgment.subject
        except JevConfigError:
            pass
    if not scope["grade"]:
        return apply_clarify(
            thread_id,
            RouteDecision(
                route="clarify",
                follow_up="请补充年级（如三年级）和知识点、题量（1–100 道）。",
                summary=getattr(decision, "summary", ""),
                count=count,
                reason="missing_grade",
            ),
        )

    query = getattr(decision, "summary", "") or transcript
    try:
        chunks = hybrid_retrieve(
            query,
            stage=scope["stage"],
            grade=scope["grade"],
            subject=scope["subject"],
            edition=scope["edition"],
            term=scope["term"],
        )
    except RetrievalError as exc:
        raise ChatError(str(exc), 503) from exc

    if not chunks:
        reply = (
            f"在{scope['grade']}{scope['subject']}{scope['edition']}{scope['term']}"
            "里没有检索到相关课文。请确认该册已入库，或换个知识点再试。"
        )
        session["messages"].append({"role": "assistant", "content": reply})
        session["draft"] = None
        persist_session(thread_id)
        return ChatTurnResult(
            status="clarifying",
            assistant_text=reply,
            summary=getattr(decision, "summary", "") or "",
            meta={**decision_to_meta(decision), **scope},
        )

    source_text = join_chunk_texts(chunks)
    summary_bit = retrieval_summary(
        chunks,
        stage=scope["stage"],
        grade=scope["grade"],
        subject=scope["subject"],
        edition=scope["edition"],
        term=scope["term"],
    )

    try:
        questions = _draft_via_agent(
            thread_id,
            transcript,
            count,
            source_text=source_text,
            grade=scope["grade"],
            subject=scope["subject"],
        )
    except BailianConfigError as exc:
        raise ChatError(str(exc), 503) from exc
    except ChatError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ChatError(f"暂时无法出题：{exc}", 503) from exc

    if not questions:
        raise ChatError("模型没有返回题目列表。", 502)

    reply = f"已根据教材内容起草 {len(questions)} 道题，请确认后生成练习卷。"
    session["messages"].append({"role": "assistant", "content": reply})
    session["draft"] = {
        "questions": questions,
        "include_answers": True,
        "count": len(questions),
        "difficulty": getattr(decision, "difficulty", None) or "适中",
    }
    summary = getattr(decision, "summary", "") or query
    session["summary"] = summary
    session["meta"] = {
        **decision_to_meta(decision),
        **scope,
        "retrieval_summary": summary_bit,
    }
    persist_session(thread_id)
    return ChatTurnResult(
        status="draft_ready",
        assistant_text=reply,
        questions=questions,
        summary=summary,
        meta=session["meta"],
    )


def apply_textbook_quiz(thread_id: str, decision) -> ChatTurnResult:
    """Supervisor textbook_quiz node: Mode A graph with chat session draft."""
    from agents.textbook.generate import TextbookError
    from agents.textbook.graph import run_textbook_quiz
    from agents.supervisor.route import RouteDecision, decision_to_meta

    session = get_session(thread_id)
    units = list(getattr(decision, "units", None) or [])
    count = getattr(decision, "count", None) or 10
    if count not in {10, 15, 20, 30}:
        # Snap to nearest allowed Mode A tier for textbook graph.
        count = min({10, 15, 20, 30}, key=lambda x: abs(x - int(count)))
    grade = getattr(decision, "grade", "") or "一年级"
    term = getattr(decision, "term", "") or "上册"
    subject = getattr(decision, "subject", "") or "数学"
    edition = getattr(decision, "edition", "") or "人教版"
    difficulty = getattr(decision, "difficulty", "") or "适中"

    if not units:
        return apply_clarify(
            thread_id,
            RouteDecision(
                route="clarify",
                follow_up="请说明要出哪一个单元（例如「一年级上册 数学游戏 出 10 道」）。",
                summary=getattr(decision, "summary", ""),
                reason="missing_units",
            ),
        )

    try:
        questions = run_textbook_quiz(
            units=units,
            count=count,
            difficulty=difficulty,
            include_answers=True,
            stage="小学",
            grade=grade,
            subject=subject,
            edition=edition,
            term=term,
        )
    except TextbookError as exc:
        return apply_clarify(
            thread_id,
            RouteDecision(
                route="clarify",
                follow_up=str(exc),
                summary=getattr(decision, "summary", ""),
                grade=grade,
                units=units,
                count=count,
                reason="textbook_error",
            ),
        )

    reply = (
        f"已按教材单元「{'、'.join(units)}」起草 {len(questions)} 道题，请确认后生成练习卷。"
    )
    session["messages"].append({"role": "assistant", "content": reply})
    session["draft"] = {
        "questions": questions,
        "include_answers": True,
        "count": len(questions),
        "difficulty": difficulty,
    }
    summary = getattr(decision, "summary", "") or f"{grade}{'、'.join(units)}"
    session["summary"] = summary
    session["meta"] = {
        **decision_to_meta(decision),
        "via": "textbook_quiz",
        "stage": "小学",
        "grade": grade,
        "subject": subject,
        "edition": edition,
        "term": term,
        "units": units,
    }
    persist_session(thread_id)
    return ChatTurnResult(
        status="draft_ready",
        assistant_text=reply,
        questions=questions,
        summary=summary,
        meta=session["meta"],
    )


def confirm_session(thread_id: str) -> dict[str, Any]:
    """Persist draft into the shared quiz store and return quiz payload fields."""
    from app.quiz_store import QuizStoreError, save_quiz

    session = get_session(thread_id)
    draft = session.get("draft")
    if not draft or not draft.get("questions"):
        raise ChatError("还没有可确认的题目，请先补充出题需求。")

    questions = draft["questions"]
    summary = session.get("summary") or "对话出题"
    title = f"对话练习 · {summary[:40]}"
    try:
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
    except QuizStoreError as exc:
        raise ChatError(str(exc), 503) from exc
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
    source_text: str | None = None,
) -> list[dict]:
    if not isinstance(count, int) or count < 1 or count > 100:
        raise ChatError("题量须为 1 至 100 道。", 400)
    grounded = (source_text or "").strip()
    if not grounded:
        raise ChatError("缺少教材检索上下文，无法出题。", 502)

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
                    f"你是{grade_bit}{subject_bit}出题助手。只根据给定课文出题，不要使用课文以外的知识点。"
                    "返回 JSON：{\"questions\":[{\"qtype\":\"选择题|填空题|计算题\",\"stem\":\"...\","
                    "\"options\":[\"A. …\",\"B. …\",\"C. …\",\"D. …\"],\"answer\":\"...\"}]}。"
                    "选择题 MUST 提供 options（至少 4 个 A-D 选项）；填空题和计算题不要 options。"
                    f"题目数量必须正好是 {count}。难度：{difficulty}。"
                    "只返回题目 JSON，不要输出思考过程。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"家长意图：{intent}\n"
                    f"课文：\n{grounded}"
                ),
            },
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


def _draft_via_agent(
    thread_id: str,
    intent: str,
    count: int,
    *,
    source_text: str,
    grade: str,
    subject: str,
) -> list[dict]:
    """Prefer DeepAgents invoke; fall back to direct grounded generation."""
    token_text = _SOURCE_TEXT.set(source_text)
    token_grade = _SOURCE_GRADE.set(grade)
    token_subject = _SOURCE_SUBJECT.set(subject)
    try:
        checkpointer = get_checkpointer()
        agent = build_agent(checkpointer=checkpointer)
        config = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": CHAT_CHECKPOINT_NS,
            }
        }
        prompt = (
            f"家长需求如下，请调用 draft_quiz 生成题目（必须紧扣已检索课文）。\n"
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
        return generate_chat_questions(
            intent=intent,
            count=count,
            grade=grade,
            subject=subject,
            source_text=source_text,
        )
    finally:
        _SOURCE_TEXT.reset(token_text)
        _SOURCE_GRADE.reset(token_grade)
        _SOURCE_SUBJECT.reset(token_subject)


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


def _retrieval_scope(transcript: str, judgment: CompletenessResult) -> dict[str, str]:
    grade = judgment.grade or ""
    subject = judgment.subject or "数学"
    term = "下册" if "下册" in transcript else "上册"
    return {
        "stage": "小学",
        "grade": grade,
        "subject": subject,
        "edition": "人教版",
        "term": term,
    }


def _default_count(text: str) -> int:
    match = re.search(r"(\d+)\s*[道题]", text)
    if match:
        value = int(match.group(1))
        if 1 <= value <= 100:
            return value
    return 10
