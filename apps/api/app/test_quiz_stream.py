"""SSE quiz route smoke tests (no live Bailian / DB)."""

from fastapi.testclient import TestClient


def test_quizzes_stream_success_and_error(monkeypatch):
    from app.main import app
    import app.routes as routes

    def success_events(**_kwargs):
        yield {
            "type": "status",
            "phase": "load_units",
            "message": "正在读取所选单元课文…",
            "total": 10,
        }
        yield {
            "type": "status",
            "phase": "generating",
            "message": "正在生成…",
            "total": 10,
        }
        questions = [{"qtype": "计算题", "stem": f"{i}+1=?"} for i in range(10)]
        yield {"type": "result", "questions": questions}

    def error_events(**_kwargs):
        yield {
            "type": "status",
            "phase": "generating",
            "message": "开始…",
            "total": 10,
        }
        yield {
            "type": "error",
            "detail": "暂时无法出题：未配置 bailian_api_key。",
            "status_code": 503,
        }

    body = {
        "stage": "小学",
        "grade": "一年级",
        "subject": "数学",
        "edition": "人教版",
        "term": "上册",
        "units": ["第一单元"],
        "count": 10,
        "difficulty": "适中",
        "include_answers": False,
    }

    monkeypatch.setattr(routes, "iter_textbook_quiz_events", success_events)
    monkeypatch.setattr(routes, "save_quiz", lambda _quiz: "quiz-stream-1")

    client = TestClient(app)
    with client.stream("POST", "/api/quizzes/stream", json=body) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        text = "".join(response.iter_text())
    assert '"type": "status"' in text or '"type":"status"' in text
    assert '"type": "done"' in text or '"type":"done"' in text
    assert "quiz-stream-1" in text
    assert "questions" in text

    monkeypatch.setattr(routes, "iter_textbook_quiz_events", error_events)
    with client.stream("POST", "/api/quizzes/stream", json=body) as response:
        assert response.status_code == 200
        text = "".join(response.iter_text())
    assert "bailian_api_key" in text
    assert '"type": "error"' in text or '"type":"error"' in text
    assert '"type": "done"' not in text and '"type":"done"' not in text
