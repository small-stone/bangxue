"""Closed-set routing for parent chat requests."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from agents.shared.bailian import BailianConfigError, build_chat_model

RouteName = Literal["clarify", "chat_draft", "textbook_quiz"]
ROUTES = frozenset({"clarify", "chat_draft", "textbook_quiz"})

RouterFn = Callable[[str], "RouteDecision"]


@dataclass
class RouteDecision:
    route: RouteName
    follow_up: str = ""
    summary: str = ""
    count: int | None = None
    grade: str = ""
    subject: str = "数学"
    term: str = "上册"
    edition: str = "人教版"
    units: list[str] = field(default_factory=list)
    difficulty: str = "适中"
    reason: str = ""


def decide_route(transcript: str, *, router: RouterFn | None = None) -> RouteDecision:
    """Return a closed route. On failure, fall back to clarify (never draft)."""
    text = (transcript or "").strip()
    if not text:
        return RouteDecision(
            route="clarify",
            follow_up="请先用一句话说明出题需求，例如年级、知识点和题量（1–100 道）。",
            reason="empty",
        )
    if router is not None:
        decision = router(text)
        return _normalize(decision)

    heuristic = _heuristic_route(text)
    if heuristic is not None:
        return heuristic

    try:
        return _normalize(_llm_route(text))
    except Exception:  # noqa: BLE001
        return RouteDecision(
            route="clarify",
            follow_up="请再补充年级或科目、知识点和题量（1–100 道），我再帮你出题。",
            reason="route_failed",
        )


def _normalize(decision: RouteDecision) -> RouteDecision:
    route = decision.route if decision.route in ROUTES else "clarify"
    if route != decision.route:
        decision = RouteDecision(
            route="clarify",
            follow_up=decision.follow_up
            or "请再补充年级或科目、知识点和题量（1–100 道）。",
            reason="invalid_route",
        )
    if decision.count is not None and (decision.count < 1 or decision.count > 100):
        return RouteDecision(
            route="clarify",
            follow_up="题量最多 100 道，请改到 1–100 之间再告诉我。",
            count=decision.count,
            reason="count_out_of_range",
        )
    decision.route = route  # type: ignore[assignment]
    return decision


def _extract_count(text: str) -> int | None:
    match = re.search(r"(\d+)\s*道", text)
    if not match:
        return None
    value = int(match.group(1))
    return value if 1 <= value <= 100 else value


def _heuristic_route(text: str) -> RouteDecision | None:
    """Cheap deterministic cues before calling the model."""
    count = _extract_count(text)
    has_topic = bool(
        re.search(r"(单元|加减|乘除|口算|认识|图形|应用题|知识|计算)", text)
    )
    has_grade = bool(re.search(r"[一二三四五六]年级", text))
    unit_match = re.search(r"(第[一二三四五六七八九十\d]+单元[^，。,. ]*|数学游戏)", text)

    if count is not None and count > 100:
        return RouteDecision(
            route="clarify",
            follow_up="题量最多 100 道，请改到 1–100 之间再告诉我。",
            count=count,
            reason="heuristic_count",
        )

    # Explicit unit + count → textbook path.
    if unit_match and count and has_grade:
        grade = re.search(r"([一二三四五六]年级)", text)
        term = "下册" if "下册" in text else "上册"
        return RouteDecision(
            route="textbook_quiz",
            summary=text[:80],
            count=count,
            grade=grade.group(1) if grade else "一年级",
            term=term,
            units=[unit_match.group(1)],
            reason="heuristic_textbook",
        )

    # Too vague → clarify.
    if count is None or (not has_topic and not has_grade and not unit_match):
        if "数学题" in text or "出题" in text or "出点" in text or len(text) < 12:
            return RouteDecision(
                route="clarify",
                follow_up="请补充年级（或学段）、具体知识点和题量（1–100 道），例如「三年级口算 12 道」。",
                reason="heuristic_clarify",
            )

    if count and (has_topic or has_grade):
        grade = re.search(r"([一二三四五六]年级)", text)
        return RouteDecision(
            route="chat_draft",
            summary=text[:80],
            count=count,
            grade=grade.group(1) if grade else "",
            reason="heuristic_chat",
        )
    return None


def _llm_route(text: str) -> RouteDecision:
    try:
        model = build_chat_model().bind(response_format={"type": "json_object"})
    except BailianConfigError:
        return RouteDecision(
            route="clarify",
            follow_up="暂时无法理解需求：未配置 bailian_api_key。请稍后重试或联系管理员。",
            reason="missing_key",
        )

    system = (
        "你是出题路由助手。只返回 JSON，不要思考过程。"
        "字段：route (clarify|chat_draft|textbook_quiz), follow_up, summary, count, "
        "grade, subject, term, edition, units (string array), difficulty, reason。"
        "信息不足用 clarify，并在 follow_up 说明可指定 1–100 道题。"
        "家长明确某年级某册某单元+题量时用 textbook_quiz，units 填单元名。"
        "其他足够意图用 chat_draft。"
    )
    from agents.shared.observability import observe_llm_call

    with observe_llm_call(path="supervisor") as handler:
        invoke_model = (
            model.with_config({"callbacks": [handler], "run_name": "supervisor-route"})
            if handler is not None
            else model
        )
        message = invoke_model.invoke(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ]
        )
    content = getattr(message, "content", None) or "{}"
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    payload = json.loads(content or "{}")
    route = str(payload.get("route") or "clarify").strip()
    units_raw = payload.get("units") or []
    units = [str(u).strip() for u in units_raw if str(u).strip()] if isinstance(units_raw, list) else []
    count_raw = payload.get("count")
    count = int(count_raw) if count_raw is not None and str(count_raw).isdigit() else None
    return RouteDecision(
        route=route if route in ROUTES else "clarify",  # type: ignore[arg-type]
        follow_up=str(payload.get("follow_up") or "").strip(),
        summary=str(payload.get("summary") or "").strip() or text[:80],
        count=count,
        grade=str(payload.get("grade") or "").strip(),
        subject=str(payload.get("subject") or "数学").strip() or "数学",
        term=str(payload.get("term") or "上册").strip() or "上册",
        edition=str(payload.get("edition") or "人教版").strip() or "人教版",
        units=units,
        difficulty=str(payload.get("difficulty") or "适中").strip() or "适中",
        reason=str(payload.get("reason") or "llm").strip() or "llm",
    )


def decision_to_meta(decision: RouteDecision) -> dict[str, Any]:
    meta: dict[str, Any] = {"supervisor_route": decision.route, "route_reason": decision.reason}
    if decision.grade:
        meta["grade"] = decision.grade
    if decision.subject:
        meta["subject"] = decision.subject
    if decision.term:
        meta["term"] = decision.term
    if decision.edition:
        meta["edition"] = decision.edition
    if decision.units:
        meta["units"] = list(decision.units)
    if decision.count is not None:
        meta["count"] = decision.count
    return meta
