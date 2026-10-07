"""Render a simple PDF for a generated paper, with optional question illustrations."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fpdf import FPDF

from agents.shared.illustrations import SceneValidationError, render_png
from app.question_format import format_question_body

_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
)


def _resolve_cjk_font() -> str:
    for path in _FONT_CANDIDATES:
        if Path(path).is_file():
            return path
    raise FileNotFoundError(
        "No CJK font found for PDF export. Install Songti (macOS) or fonts-wqy-zenhei (Linux)."
    )


def render_pdf(
    *,
    title: str,
    lines: list[str] | None = None,
    questions: list[dict] | None = None,
    include_answer: bool = False,
) -> bytes:
    """Render PDF from plain lines (legacy) or structured questions with illustrations."""
    pdf = FPDF()
    pdf.add_font("Songti", fname=_resolve_cjk_font())
    pdf.set_font("Songti", size=14)
    pdf.add_page()
    pdf.multi_cell(0, 10, title)
    pdf.ln(4)
    pdf.set_font("Songti", size=12)

    if questions is not None:
        for index, item in enumerate(questions, start=1):
            body = format_question_body(item, include_answer=include_answer)
            pdf.multi_cell(0, 8, f"{index}. {body}")
            _embed_illustration(pdf, item)
            pdf.ln(2)
    else:
        for index, line in enumerate(lines or [], start=1):
            pdf.multi_cell(0, 8, f"{index}. {line}")
            pdf.ln(2)

    return bytes(pdf.output())


def _embed_illustration(pdf: FPDF, item: dict) -> None:
    illustration = item.get("illustration") or {}
    scene = illustration.get("scene")
    if not isinstance(scene, dict):
        return
    try:
        png = render_png(scene, scale=2)
    except (SceneValidationError, TypeError, ValueError):
        return

    # fpdf needs a filesystem path for PNG embedding.
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(png)
        path = tmp.name
    try:
        max_w = pdf.epw * 0.92
        pdf.ln(1)
        pdf.image(path, w=max_w)
        pdf.ln(2)
    finally:
        Path(path).unlink(missing_ok=True)
