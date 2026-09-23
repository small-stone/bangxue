"""Render a simple text PDF for a generated paper."""

from fpdf import FPDF

_FONT = "/System/Library/Fonts/Supplemental/Songti.ttc"


def render_pdf(*, title: str, lines: list[str]) -> bytes:
    pdf = FPDF()
    pdf.add_font("Songti", fname=_FONT)
    pdf.set_font("Songti", size=14)
    pdf.add_page()
    pdf.multi_cell(0, 10, title)
    pdf.ln(4)
    pdf.set_font("Songti", size=12)
    for index, line in enumerate(lines, start=1):
        pdf.multi_cell(0, 8, f"{index}. {line}")
        pdf.ln(2)
    return bytes(pdf.output())
