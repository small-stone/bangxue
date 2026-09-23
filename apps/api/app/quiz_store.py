"""In-memory quiz papers for the current API process."""

from uuid import uuid4

_QUIZZES: dict[str, dict] = {}


def save_quiz(quiz: dict) -> str:
    quiz_id = uuid4().hex
    _QUIZZES[quiz_id] = quiz
    return quiz_id


def get_quiz(quiz_id: str) -> dict | None:
    return _QUIZZES.get(quiz_id)
