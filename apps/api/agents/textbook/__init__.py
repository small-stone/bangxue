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

placeholder = "textbook"


def build_graph():
    """Return the textbook StateGraph once the full workflow exists."""
    return None
