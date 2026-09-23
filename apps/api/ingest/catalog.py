"""Discover primary-math PDFs under book/ and parse grade/term metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_GRADES = ("一年级", "二年级", "三年级", "四年级", "五年级", "六年级")
_TERMS = ("上册", "下册")
_GRADE_RE = re.compile("|".join(_GRADES))
_TERM_RE = re.compile("|".join(_TERMS))


@dataclass(frozen=True)
class BookTarget:
    pdf: Path
    stage: str
    grade: str
    subject: str
    edition: str
    term: str


def default_primary_math_root() -> Path:
    # apps/api/ingest/catalog.py -> repo root
    return Path(__file__).resolve().parents[3] / "book" / "小学" / "数学"


def discover_primary_math_pdfs(root: Path | None = None) -> list[Path]:
    base = root or default_primary_math_root()
    if not base.is_dir():
        return []
    return sorted(base.rglob("*.pdf"))


def parse_primary_math_meta(pdf: Path) -> BookTarget:
    """Parse grade/term from filename; stage/subject/edition come from the folder layout."""
    name = pdf.name
    grade_match = _GRADE_RE.search(name)
    term_match = _TERM_RE.search(name)
    if not grade_match or not term_match:
        raise ValueError(f"Cannot parse grade/term from filename: {pdf.name}")
    edition = "人教版"
    for part in pdf.parts:
        if part in {"人教版", "苏教版", "北师大版", "沪教版"}:
            edition = part
            break
    return BookTarget(
        pdf=pdf,
        stage="小学",
        grade=grade_match.group(0),
        subject="数学",
        edition=edition,
        term=term_match.group(0),
    )
