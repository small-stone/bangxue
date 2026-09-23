"""Textbook generation agent, called in-process by FastAPI."""

from agents.textbook.generate import (
    ALLOWED_BOOK,
    TextbookError,
    generate_questions,
    is_allowed_book,
    list_units,
    load_unit_text,
)

placeholder = "textbook"


def build_graph():
    """Return the textbook StateGraph once the full workflow exists."""
    return None
