"""Split extracted pages on textbook unit headings."""

import re
from dataclasses import dataclass

# "第一单元 …" or "第 1 单元 …" on one line.
_INLINE_UNIT = re.compile(
    r"第\s*[0-9０-９一二三四五六七八九十百零〇]+\s*单\s*元"
)
# PEP books often put the unit index alone: "一" then the title on the next line.
_LONE_INDEX = re.compile(r"^[一二三四五六七八九十]$")
_TOC_PAGE_NUM = re.compile(r"\d{1,3}$")
_CN_ORDINAL = {
    "一": "第一单元",
    "二": "第二单元",
    "三": "第三单元",
    "四": "第四单元",
    "五": "第五单元",
    "六": "第六单元",
    "七": "第七单元",
    "八": "第八单元",
    "九": "第九单元",
    "十": "第十单元",
}


class UnitSplitError(Exception):
    """Raised when no unit headings can be found."""


@dataclass(frozen=True)
class Chunk:
    unit_name: str
    page_start: int
    page_end: int
    content: str


def split_pages(pages: list[tuple[int, str]], max_chars: int = 800) -> list[Chunk]:
    """Split pages into unit chunks. Fail when no unit heading exists."""
    spans = _unit_spans(pages)
    if not spans:
        raise UnitSplitError(
            "No unit headings found. Refusing to store a book without unit markers."
        )
    chunks: list[Chunk] = []
    for unit_name, page_start, page_end, text in spans:
        for piece in _subsplit(text, max_chars):
            cleaned = piece.strip()
            if cleaned:
                chunks.append(
                    Chunk(
                        unit_name=unit_name,
                        page_start=page_start,
                        page_end=page_end,
                        content=cleaned,
                    )
                )
    if not chunks:
        raise UnitSplitError("Unit headings were found but no body text was extracted.")
    return chunks


def _unit_spans(pages: list[tuple[int, str]]) -> list[tuple[str, int, int, str]]:
    lines = _flat_lines(pages)
    current_name: str | None = None
    current_start = 0
    current_end = 0
    current_lines: list[str] = []
    spans: list[tuple[str, int, int, str]] = []

    def flush() -> None:
        if current_name is None:
            return
        spans.append(
            (current_name, current_start, current_end, "\n".join(current_lines))
        )

    index = 0
    while index < len(lines):
        page_no, line = lines[index]
        heading, skip = _heading_at(lines, index)
        if heading is None:
            if current_name is not None:
                current_end = page_no
                current_lines.append(line)
            index += 1
            continue
        flush()
        current_name = heading
        current_start = page_no
        current_end = page_no
        current_lines = [heading]
        index += skip
    flush()
    return spans


def _flat_lines(pages: list[tuple[int, str]]) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for page_no, text in pages:
        if _is_toc_page(text):
            continue
        for raw in text.splitlines():
            line = raw.strip()
            if line:
                lines.append((page_no, line))
    return lines


def _is_toc_page(text: str) -> bool:
    for raw in text.splitlines():
        if raw.strip():
            return raw.strip() == "目录"
    return False


def _heading_at(lines: list[tuple[int, str]], index: int) -> tuple[str | None, int]:
    """Return (unit_name, lines_consumed) or (None, 1) when this line is body text."""
    _page_no, line = lines[index]
    if line == "学习准备":
        return "学习准备", 1
    if _INLINE_UNIT.search(line) and len(line) <= 40:
        return re.sub(r"\s+", "", line), 1
    if _LONE_INDEX.match(line) and index + 1 < len(lines):
        title = lines[index + 1][1]
        if title.startswith("年") or len(title) < 4 or _TOC_PAGE_NUM.search(title):
            return None, 1
        name = _CN_ORDINAL[line] + re.sub(r"\s+", "", title)
        return name, 2
    return None, 1


def _subsplit(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    buffer = ""
    for paragraph in re.split(r"\n+", text):
        if buffer and len(buffer) + len(paragraph) + 1 > max_chars:
            parts.append(buffer)
            buffer = paragraph
        elif buffer:
            buffer = f"{buffer}\n{paragraph}"
        else:
            buffer = paragraph
    if buffer:
        parts.append(buffer)
    return parts
