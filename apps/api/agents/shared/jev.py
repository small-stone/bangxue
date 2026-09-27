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
MISSING_GRADE = "grade"
MISSING_SUBJECT = "subject"

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
    if subject is None and _looks_like_math(text):
        subject = "数学"

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
    if not topic_ok:
        missing.append(MISSING_TOPIC)
    if grade is None:
        missing.append(MISSING_GRADE)
    if subject is None:
        missing.append(MISSING_SUBJECT)

    # Deduplicate while preserving order
    deduped: list[str] = []
    seen: set[str] = set()
    for item in missing:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    missing = deduped

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


def _looks_like_math(text: str) -> bool:
    math_hints = (
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
        "计算",
        "数学",
    )
    return any(hint in text for hint in math_hints)


def _extract_subject(text: str) -> str | None:
    for name in ("数学", "英语", "语文"):
        if name in text:
            return name
    return None


_GRADE_NAMES = ("一年级", "二年级", "三年级", "四年级", "五年级", "六年级")
_GRADE_BY_DIGIT = {
    "1": "一年级",
    "2": "二年级",
    "3": "三年级",
    "4": "四年级",
    "5": "五年级",
    "6": "六年级",
}
# Arabic / fullwidth digits: "3年级", "３ 年级"
_GRADE_DIGIT_RE = re.compile(r"(?P<n>[1-6１-６])\s*年级")


def _extract_grade(text: str) -> str | None:
    """Return the last explicit primary grade (Chinese or digit form)."""
    hits: list[tuple[int, str]] = []
    for name in _GRADE_NAMES:
        start = 0
        while True:
            idx = text.find(name, start)
            if idx < 0:
                break
            hits.append((idx, name))
            start = idx + 1
    for match in _GRADE_DIGIT_RE.finditer(text):
        digit = match.group("n")
        # Normalize fullwidth １–６ to ASCII
        if "１" <= digit <= "６":
            digit = chr(ord("1") + (ord(digit) - ord("１")))
        name = _GRADE_BY_DIGIT.get(digit)
        if name:
            hits.append((match.start(), name))
    if not hits:
        return None
    hits.sort(key=lambda item: item[0])
    return hits[-1][1]


def _follow_up_for(missing: list[str]) -> str:
    if not missing:
        return ""
    parts: list[str] = []
    if MISSING_GRADE in missing:
        parts.append("年级（例如一年级）")
    if MISSING_SUBJECT in missing:
        parts.append("科目（数学 / 语文 / 英语）")
    if MISSING_TOPIC in missing:
        parts.append("具体知识点或题型（例如两位数加减、口算）")
    if MISSING_COUNT in missing:
        parts.append(f"题量（1–{_MAX_COUNT} 道）")
    joined = "、".join(parts)
    return f"为了按教材出合适的练习，请再补充：{joined}。"
