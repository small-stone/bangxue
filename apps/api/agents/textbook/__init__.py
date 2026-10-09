"""Textbook generation agent, called in-process by FastAPI."""

from agents.textbook.generate import (
    PRIMARY_GRADES,
    PRIMARY_TERMS,
    TextbookError,
    generate_questions,
    is_allowed_book,
    list_units,
    load_unit_text,
)
from agents.textbook.graph import build_graph, run_textbook_quiz
from agents.textbook.stream import collect_textbook_questions, iter_textbook_quiz_events

placeholder = "textbook"

__all__ = [
    "PRIMARY_GRADES",
    "PRIMARY_TERMS",
    "TextbookError",
    "build_graph",
    "collect_textbook_questions",
    "generate_questions",
    "is_allowed_book",
    "iter_textbook_quiz_events",
    "list_units",
    "load_unit_text",
    "placeholder",
    "run_textbook_quiz",
]
