"""Grade-one through grade-six primary math generation from ingested chunks."""

import json
from collections.abc import Callable, Sequence

import psycopg

from ingest.store import connect

PRIMARY_GRADES = {"一年级", "二年级", "三年级", "四年级", "五年级", "六年级"}
PRIMARY_TERMS = {"上册", "下册"}

Generator = Callable[..., list[dict]]


class TextbookError(Exception):
    """User-facing generation or lookup failure."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def is_allowed_book(**meta: str) -> bool:
    return (
        meta.get("stage") == "小学"
        and meta.get("subject") == "数学"
        and meta.get("edition") == "人教版"
        and meta.get("grade") in PRIMARY_GRADES
        and meta.get("term") in PRIMARY_TERMS
    )


def list_units(**meta: str) -> list[str]:
    _require_primary_math(**meta)
    try:
        with connect() as conn:
            names = _unit_names(conn, meta)
    except RuntimeError as exc:
        raise TextbookError(str(exc), 503) from exc
    if not names:
        raise TextbookError("该册尚未入库，请先完成教材入库。", 404)
    return names


def load_unit_text(units: Sequence[str], **meta: str) -> str:
    _require_primary_math(**meta)
    if not units:
        raise TextbookError("请至少选择一个单元。")
    try:
        conn_cm = connect()
    except RuntimeError as exc:
        raise TextbookError(str(exc), 503) from exc
    with conn_cm as conn:
        known = set(_unit_names(conn, meta))
        if not known:
            raise TextbookError("该册尚未入库，请先完成教材入库。", 404)
        missing = [name for name in units if name not in known]
        if missing:
            raise TextbookError(f"单元尚未入库：{'、'.join(missing)}", 404)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT unit_name, content
                FROM textbook_chunks
                WHERE stage = %s AND grade = %s AND subject = %s
                  AND edition = %s AND term = %s
                  AND unit_name = ANY(%s)
                ORDER BY page_start, id
                """,
                (
                    meta["stage"],
                    meta["grade"],
                    meta["subject"],
                    meta["edition"],
                    meta["term"],
                    list(units),
                ),
            )
            rows = cur.fetchall()
    if not rows:
        raise TextbookError("所选单元没有可用课文。", 404)
    parts: list[str] = []
    used = 0
    for unit_name, content in rows:
        piece = content.strip()
        if not piece or used > 8000:
            continue
        parts.append(f"【{unit_name}】\n{piece}")
        used += len(piece)
    return "\n\n".join(parts)


def generate_questions(
    *,
    source_text: str,
    count: int,
    difficulty: str,
    include_answers: bool,
    grade: str = "一年级",
    generator: Generator | None = None,
) -> list[dict]:
    """Facade: run the textbook LangGraph with preloaded source text."""
    from agents.textbook.graph import run_textbook_quiz

    return run_textbook_quiz(
        units=[],
        count=count,
        difficulty=difficulty,
        include_answers=include_answers,
        generator=generator,
        source_text=source_text,
        stage="小学",
        grade=grade,
        subject="数学",
        edition="人教版",
        term="上册",
    )


def _require_primary_math(**meta: str) -> None:
    if not is_allowed_book(**meta):
        raise TextbookError("目前只能出小学数学人教版一年级至六年级的上册或下册。")


def _unit_names(conn: psycopg.Connection, meta: dict[str, str]) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT unit_name
            FROM textbook_chunks
            WHERE stage = %s AND grade = %s AND subject = %s
              AND edition = %s AND term = %s
            GROUP BY unit_name
            ORDER BY min(page_start), unit_name
            """,
            (meta["stage"], meta["grade"], meta["subject"], meta["edition"], meta["term"]),
        )
        return [row[0] for row in cur.fetchall()]


def _bailian_generator(**kwargs) -> list[dict]:
    """One-shot JSON quiz generation via the shared Bailian chat model factory."""
    from agents.shared.bailian import BailianConfigError, build_chat_model

    try:
        model = build_chat_model().bind(response_format={"type": "json_object"})
    except BailianConfigError as exc:
        raise TextbookError(str(exc), 503) from exc

    include_answers = kwargs["include_answers"]
    grade = kwargs.get("grade") or "一年级"
    answer_rule = "每题包含 answer。" if include_answers else "不要包含 answer 字段。"
    system = (
        f"你是{grade}小学数学出题助手。只根据给定课文出题，不要使用课文以外的知识点。"
        "返回 JSON：{\"questions\":[{\"qtype\":\"选择题|填空题|计算题\",\"stem\":\"...\","
        "\"options\":[\"A. …\",\"B. …\",\"C. …\",\"D. …\"],"
        "\"scene\":{\"kind\":\"row_of_groups\",\"item\":\"fish|strawberry|apple|star|circle\","
        "\"groups\":[{\"count\":1to10}]}}]}。"
        "选择题 MUST 提供 options（至少 4 个 A-D 选项）；填空题和计算题不要 options。"
        "若题干依赖看图数一数/合起来，MUST 附带 scene（kind 固定为 row_of_groups；"
        "groups[].count 之和或序数须与题干和答案一致；每组 count 为 1–10）。"
        "纯计算或不依赖图示的题 MUST NOT 带 scene。"
        "禁止用「见课文插图」代替 scene；不要输出 SVG 或图片 URL。"
        f"题目数量必须正好是指定数量。{answer_rule}"
        "只返回题目 JSON，不要输出思考过程。"
    )
    user = (
        f"难度：{kwargs['difficulty']}\n"
        f"题量：{kwargs['count']}\n"
        "题型比例：选择题 40%，填空题 30%，计算题 30%。\n"
        "若课文涉及数一数/合起来/看图，请至少出一部分带 scene 的看图题。\n"
        f"课文：\n{kwargs['source_text']}"
    )
    try:
        message = model.invoke(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
    except Exception as exc:  # noqa: BLE001
        raise TextbookError(f"暂时无法出题：{exc}", 503) from exc

    content = getattr(message, "content", None) or ""
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    try:
        payload = json.loads(content or "{}")
    except json.JSONDecodeError as exc:
        raise TextbookError("模型没有返回合法 JSON。", 502) from exc
    questions = payload.get("questions")
    if not isinstance(questions, list):
        raise TextbookError("模型没有返回题目列表。", 502)
    return questions
