"""Grade-one through grade-six primary math generation from ingested chunks."""

import json
import os
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
    api_key = os.environ.get("bailian_api_key")
    if not api_key:
        raise TextbookError("暂时无法出题：未配置 bailian_api_key。", 503)
    from openai import OpenAI

    model = os.environ.get("QUIZ_MODEL", "qwen3.7-plus")
    base_url = os.environ.get(
        "BAILIAN_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    include_answers = kwargs["include_answers"]
    grade = kwargs.get("grade") or "一年级"
    answer_rule = "每题包含 answer。" if include_answers else "不要包含 answer 字段。"
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        extra_body={"enable_thinking": False},
        messages=[
            {
                "role": "system",
                "content": (
                    f"你是{grade}小学数学出题助手。只根据给定课文出题，不要使用课文以外的知识点。"
                    "返回 JSON：{\"questions\":[{\"qtype\":\"选择题|填空题|计算题\",\"stem\":\"...\","
                    "\"options\":[\"A. …\",\"B. …\",\"C. …\",\"D. …\"]}]}。"
                    "选择题 MUST 提供 options（至少 4 个 A-D 选项）；填空题和计算题不要 options。"
                    f"题目数量必须正好是指定数量。{answer_rule}"
                    "只返回题目 JSON，不要输出思考过程。"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"难度：{kwargs['difficulty']}\n"
                    f"题量：{kwargs['count']}\n"
                    "题型比例：选择题 40%，填空题 30%，计算题 30%。\n"
                    f"课文：\n{kwargs['source_text']}"
                ),
            },
        ],
    )
    message = response.choices[0].message
    payload = json.loads(message.content or "{}")
    questions = payload.get("questions")
    if not isinstance(questions, list):
        raise TextbookError("模型没有返回题目列表。", 502)
    return questions
