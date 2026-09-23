"""Grade-one math question generation from ingested textbook chunks."""

import json
import os
from collections.abc import Callable, Sequence

import psycopg

from ingest.store import connect

ALLOWED_BOOK = {
    "stage": "小学",
    "grade": "一年级",
    "subject": "数学",
    "edition": "人教版",
    "term": "上册",
}

Generator = Callable[..., list[dict]]


class TextbookError(Exception):
    """User-facing generation or lookup failure."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def is_allowed_book(**meta: str) -> bool:
    return all(meta.get(key) == value for key, value in ALLOWED_BOOK.items())


def list_units(**meta: str) -> list[str]:
    if not is_allowed_book(**meta):
        raise TextbookError("目前只能出小学一年级数学人教版上册。")
    try:
        with connect() as conn:
            return _unit_names(conn, meta)
    except RuntimeError as exc:
        raise TextbookError(str(exc), 503) from exc


def load_unit_text(units: Sequence[str], **meta: str) -> str:
    if not is_allowed_book(**meta):
        raise TextbookError("目前只能出小学一年级数学人教版上册。")
    if not units:
        raise TextbookError("请至少选择一个单元。")
    try:
        conn_cm = connect()
    except RuntimeError as exc:
        raise TextbookError(str(exc), 503) from exc
    with conn_cm as conn:
        known = set(_unit_names(conn, meta))
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
    generator: Generator | None = None,
) -> list[dict]:
    if count not in {10, 15, 20, 30}:
        raise TextbookError("题量只能是 10、15、20 或 30。")
    build = generator or _bailian_generator
    try:
        questions = build(
            source_text=source_text,
            count=count,
            difficulty=difficulty,
            include_answers=include_answers,
        )
    except TextbookError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface provider failures as config errors
        raise TextbookError(f"暂时无法出题：{exc}", 503) from exc
    if len(questions) != count:
        raise TextbookError("题目数量与设置不一致，请重试。", 502)
    cleaned: list[dict] = []
    for item in questions:
        stem = str(item.get("stem", "")).strip()
        if not stem:
            raise TextbookError("生成结果缺少题干。", 502)
        row = {"qtype": str(item.get("qtype") or "计算题"), "stem": stem}
        if include_answers:
            row["answer"] = str(item.get("answer", "")).strip()
        cleaned.append(row)
    return cleaned


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
                    "你是小学数学出题助手。只根据给定课文出题，不要使用课文以外的知识点。"
                    "返回 JSON：{\"questions\":[{\"qtype\":\"选择题|填空题|计算题\",\"stem\":\"...\"}]}。"
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
