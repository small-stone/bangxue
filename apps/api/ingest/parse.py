"""Extract per-page text from a textbook PDF."""

import warnings
from pathlib import Path

import pdfplumber

# Some textbook PDFs use a color space pdfminer warns about on every page.
warnings.filterwarnings("ignore", message="Cannot set non-stroke color")


def extract_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """Return 1-based page numbers and their extracted text."""
    pages: list[tuple[int, str]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append((index, text))
    return pages
