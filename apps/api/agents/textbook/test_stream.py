"""Event-order tests for the textbook quiz streaming pipeline."""

import pytest

from agents.textbook.generate import TextbookError
from agents.textbook.stream import collect_textbook_questions, iter_textbook_quiz_events


def _fake_questions(count: int, *, include_answers: bool) -> list[dict]:
    rows = []
    for index in range(count):
        row: dict = {
            "qtype": "计算题",
            "stem": f"1 + {index} = ?",
        }
        if include_answers:
            row["answer"] = str(1 + index)
        rows.append(row)
    return rows


def test_iter_events_order_with_fake_generator():
    count = 10
    events = list(
        iter_textbook_quiz_events(
            units=["单元1"],
            count=count,
            difficulty="适中",
            include_answers=False,
            generator=lambda **kwargs: _fake_questions(
                kwargs["count"], include_answers=kwargs["include_answers"]
            ),
            source_text="1+1=2",
            stage="小学",
            grade="一年级",
            subject="数学",
            edition="人教版",
            term="上册",
        )
    )
    types = [event["type"] for event in events]
    assert types[0] == "status"
    assert events[0]["phase"] == "load_units"
    phases = {e.get("phase") for e in events if e["type"] == "status"}
    assert "generating" in phases
    assert "validating" in phases
    assert types.count("question") == count
    assert types[-1] == "result"
    assert len(events[-1]["questions"]) == count
    collected = collect_textbook_questions(
        units=["单元1"],
        count=count,
        difficulty="适中",
        include_answers=True,
        generator=lambda **kwargs: _fake_questions(
            kwargs["count"], include_answers=kwargs["include_answers"]
        ),
        source_text="1+1=2",
        stage="小学",
        grade="一年级",
        subject="数学",
        edition="人教版",
        term="上册",
    )
    assert len(collected) == count
    assert all("answer" in row for row in collected)


def test_collect_raises_config_error():
    with pytest.raises(TextbookError) as caught:
        collect_textbook_questions(
            units=["单元1"],
            count=10,
            difficulty="适中",
            include_answers=False,
            generator=lambda **_kwargs: (_ for _ in ()).throw(
                TextbookError("暂时无法出题：未配置 bailian_api_key。", 503)
            ),
            source_text="text",
            stage="小学",
            grade="一年级",
            subject="数学",
            edition="人教版",
            term="上册",
        )
    assert caught.value.status_code == 503
    assert "bailian_api_key" in str(caught.value)
