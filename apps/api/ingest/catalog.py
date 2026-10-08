"""Discover primary-school textbook PDFs under book/ and parse metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_GRADES = ("一年级", "二年级", "三年级", "四年级", "五年级", "六年级")
_TERMS = ("上册", "下册")
_GRADE_RE = re.compile("|".join(_GRADES))
_TERM_RE = re.compile("|".join(_TERMS))
_KNOWN_EDITIONS = {"人教版", "苏教版", "北师大版", "沪教版", "统编版"}
# Folder names like "人教版（主编：吴欣）" collapse to the base edition label.
_EDITION_PREFIXES = ("人教版", "苏教版", "北师大版", "沪教版", "统编版")
_SUBJECT_DEFAULT_EDITION = {
    "数学": "人教版",
    "语文": "统编版",
    "英语": "人教版",
}


@dataclass(frozen=True)
class BookTarget:
    pdf: Path
    stage: str
    grade: str
    subject: str
    edition: str
    term: str


def default_primary_subject_root(subject: str) -> Path:
    # apps/api/ingest/catalog.py -> repo root
    return Path(__file__).resolve().parents[3] / "book" / "小学" / subject


def default_primary_math_root() -> Path:
    return default_primary_subject_root("数学")


def discover_primary_pdfs(subject: str, root: Path | None = None) -> list[Path]:
    base = root or default_primary_subject_root(subject)
    if not base.is_dir():
        return []
    pdfs = sorted(base.rglob("*.pdf"))
    return _dedupe_grade_term(pdfs, subject)


def _dedupe_grade_term(pdfs: list[Path], subject: str) -> list[Path]:
    """Keep one PDF per grade+term when folders contain duplicate scans."""
    best: dict[tuple[str, str], Path] = {}
    leftovers: list[Path] = []
    for pdf in pdfs:
        try:
            meta = parse_primary_meta(pdf, subject)
        except ValueError:
            leftovers.append(pdf)
            continue
        key = (meta.grade, meta.term)
        current = best.get(key)
        if current is None or _pdf_rank(pdf) > _pdf_rank(current):
            best[key] = pdf
    chosen = sorted(best.values(), key=lambda path: path.as_posix())
    return chosen + leftovers


def _pdf_rank(pdf: Path) -> tuple[int, int, int]:
    name = pdf.name
    # Prefer 2022-revision scans and bullet-separated titles over spaced duplicates.
    return (
        1 if "2022" in name else 0,
        1 if "•" in name or "·" in name else 0,
        len(name),
    )


def discover_primary_math_pdfs(root: Path | None = None) -> list[Path]:
    return discover_primary_pdfs("数学", root)


def _edition_from_path(pdf: Path, subject: str) -> str:
    default = _SUBJECT_DEFAULT_EDITION.get(subject, "人教版")
    for part in pdf.parts:
        if part in _KNOWN_EDITIONS:
            return part
        for prefix in _EDITION_PREFIXES:
            if part.startswith(prefix):
                return prefix
    return default


def parse_primary_meta(pdf: Path, subject: str) -> BookTarget:
    """Parse grade/term from filename; stage/subject/edition from folder layout."""
    # "（三年级起点）五年级下册" must not parse the annotation as the grade.
    name = (
        pdf.name.replace("（三年级起点）", " ")
        .replace("(三年级起点)", " ")
        .replace("三年级起点", " ")
    )
    grade_match = _GRADE_RE.search(name)
    term_match = _TERM_RE.search(name)
    if not grade_match or not term_match:
        raise ValueError(f"Cannot parse grade/term from filename: {pdf.name}")
    return BookTarget(
        pdf=pdf,
        stage="小学",
        grade=grade_match.group(0),
        subject=subject,
        edition=_edition_from_path(pdf, subject),
        term=term_match.group(0),
    )


def parse_primary_math_meta(pdf: Path) -> BookTarget:
    return parse_primary_meta(pdf, "数学")
