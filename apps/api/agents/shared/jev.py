"""Flow judgment client for chat intake completeness (Jev / TypeSafe).

Until the TypeSafe SDK schema is wired, a closed-form local judge runs only
when TYPESAFE_API_KEY is present. Missing key never invents an \"enough\" result.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

class JevConfigError(RuntimeError):
    """Missing Jev / TypeSafe configuration."""


MISSING_COUNT = "count"
MISSING_TOPIC = "topic"
MISSING_COUNT_RANGE = "count_range"

_MAX_COUNT = 100

_COUNT_RE = re.compile(
    r"(?P<n>\d+)\s*[道题]|(?P<n2>十|十五|二十|三十)\s*[道题]|题量\s*(?P<n3>\d+)|出\s*(?P<n4>\d+)"
)
_TOPIC_HINTS = (
    "口算",
    "加减",
    "乘除",
    "乘法",
    "除法",
    "分数",
    "小数",
    "应用题",
    "几何",
    "面积",
    "周长",
    "体积",
    "单位换算",
    "认识",
    "比较",
    "填空",
    "选择",
    "判断",
    "计算",
    "英语",
    "单词",
    "语法",
    "阅读",
    "语文",
    "拼音",
    "生字",
)


@dataclass(frozen=True)
class CompletenessResult:
    enough: bool
    confidence: float
    missing: tuple[str, ...]
    follow_up: str
    summary: str
    count: int | None = None
    subject: str | None = None
    grade: str | None = None


def require_typesafe_api_key() -> str:
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise JevConfigError("暂时无法判断出题信息是否足够：未配置 TYPESAFE_API_KEY。")
    return key


def judge_chat_completeness(transcript: str) -> CompletenessResult:
    """Return whether the parent dialogue is enough to draft questions.

    Requires TYPESAFE_API_KEY. Optional JEV_ENDPOINT calls a remote judge;
    otherwise uses the interim local closed-form judge (same enough/missing closure).
    """
    require_typesafe_api_key()
    endpoint = os.environ.get("JEV_ENDPOINT", "").strip()
    if endpoint:
        return _remote_completeness(endpoint, transcript)
    return _local_completeness(transcript)


def _remote_completeness(endpoint: str, transcript: str) -> CompletenessResult:
    # Placeholder for TypeSafe HTTP; fail closed rather than inventing "enough".
    raise JevConfigError(
        f"JEV_ENDPOINT 已配置但远程客户端尚未接入（{endpoint}）。请暂时去掉该变量以使用本地封闭判断。"
    )


def _local_completeness(transcript: str) -> CompletenessResult:
    text = (transcript or "").strip()
    missing: list[str] = []
    count = _extract_count(text)
    topic_ok = _has_topic(text)
    subject = _extract_subject(text)
    grade = _extract_grade(text)

    if count is not None and count > _MAX_COUNT:
        return CompletenessResult(
            enough=False,
            confidence=0.95,
            missing=(MISSING_COUNT_RANGE,),
            follow_up=f"题量最多 {_MAX_COUNT} 道，请改到 1–{_MAX_COUNT} 之间再告诉我。",
            summary=text[:80] if text else "对话出题",
            count=count,
            subject=subject,
            grade=grade,
        )

    if count is None or count < 1:
        missing.append(MISSING_COUNT)
        count = None
    if not topic_ok and not (subject and grade and count is not None):
        if not topic_ok:
            missing.append(MISSING_TOPIC)

    if subject and not topic_ok and count is None:
        missing = [MISSING_COUNT, MISSING_TOPIC]

    enough = not missing
    confidence = 0.9 if enough else 0.85
    follow_up = _follow_up_for(missing)
    summary = text[:80] if text else "对话出题"
    return CompletenessResult(
        enough=enough,
        confidence=confidence,
        missing=tuple(missing),
        follow_up=follow_up,
        summary=summary,
        count=count,
        subject=subject,
        grade=grade,
    )


def _extract_count(text: str) -> int | None:
    """Return the last explicit count mentioned in the transcript."""
    matches = list(_COUNT_RE.finditer(text))
    if not matches:
        return None
    match = matches[-1]
    raw = match.group("n") or match.group("n3") or match.group("n4")
    if raw:
        return int(raw)
    word = match.group("n2")
    return {"十": 10, "十五": 15, "二十": 20, "三十": 30}.get(word or "", None)


def _has_topic(text: str) -> bool:
    return any(hint in text for hint in _TOPIC_HINTS)


def _extract_subject(text: str) -> str | None:
    for name in ("数学", "英语", "语文"):
        if name in text:
            return name
    return None


def _extract_grade(text: str) -> str | None:
    for name in ("一年级", "二年级", "三年级", "四年级", "五年级", "六年级"):
        if name in text:
            return name
    return None


def _follow_up_for(missing: list[str]) -> str:
    if not missing:
        return ""
    parts: list[str] = []
    if MISSING_TOPIC in missing:
        parts.append("具体知识点或题型（例如两位数加减、口算）")
    if MISSING_COUNT in missing:
        parts.append(f"题量（1–{_MAX_COUNT} 道）")
    joined = "、".join(parts)
    return f"为了帮孩子出合适的练习，请再补充：{joined}。"
