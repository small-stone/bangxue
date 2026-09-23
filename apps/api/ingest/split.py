"""Split extracted pages on textbook unit headings."""

import re
from dataclasses import dataclass

# "第一单元 …" or "第 1 单元 …" on one line.
_INLINE_UNIT = re.compile(
    r"第\s*[0-9０-９一二三四五六七八九十百零〇]+\s*单\s*元"
)
# PEP 2022-style books put the unit index alone: "一" then the title on the next line.
_LONE_INDEX = re.compile(r"^[一二三四五六七八九十]$")
# Older PEP TOC lines: "1 四则运算" optionally followed by a page number line.
_ARABIC_TOC_ENTRY = re.compile(r"^(\d{1,2})\s+(.+)$")
# 2022 TOC title lines often end with the printed page number.
_TITLE_WITH_PAGE = re.compile(r"^(.+?)\s+(\d{1,3})$")
_TOC_PAGE_NUM = re.compile(r"^\d{1,3}$")
_HAS_CJK = re.compile(r"[\u4e00-\u9fff]")
_STANDALONE_TITLES = {"学习准备", "总复习", "数学游戏"}
_WATERMARK = "仅供个人学习使用"
_NOISE_TITLE = re.compile(r"[？?。=÷×＋+\-−]|做一做|练一练|试一试|练习[一二三四五六七八九十\d]")
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
_ARABIC_ORDINAL = {
    "1": "第一单元",
    "2": "第二单元",
    "3": "第三单元",
    "4": "第四单元",
    "5": "第五单元",
    "6": "第六单元",
    "7": "第七单元",
    "8": "第八单元",
    "9": "第九单元",
    "10": "第十单元",
    "11": "第十一单元",
    "12": "第十二单元",
}


class UnitSplitError(Exception):
    """Raised when no unit headings can be found."""


@dataclass(frozen=True)
class Chunk:
    unit_name: str
    page_start: int
    page_end: int
    content: str


@dataclass(frozen=True)
class _TocEntry:
    unit_name: str
    title: str
    page_hint: int


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
    toc_entries, toc_pages = _collect_toc(pages)
    if len(toc_entries) >= 3:
        spans = _spans_from_toc(pages, toc_entries, toc_pages)
        # Prefer TOC when most chapters were located; otherwise fall back.
        if len(spans) >= max(3, (len(toc_entries) + 1) // 2):
            return spans
    return _spans_from_cn_headings(pages, toc_pages)


def _collect_toc(
    pages: list[tuple[int, str]],
) -> tuple[list[_TocEntry], set[int]]:
    """Parse the table of contents. Returns validated entries and TOC page numbers."""
    collecting = False
    toc_pages: set[int] = set()
    raw: list[_TocEntry] = []
    pending_cn: str | None = None
    pending_arabic: tuple[str, str] | None = None
    toc_page_budget = 0

    for page_no, text in pages:
        lines = [raw_line.strip() for raw_line in text.splitlines() if raw_line.strip()]
        if not lines:
            continue
        first = re.sub(r"\s+", "", lines[0])
        if first in {"目录", "目錄"}:
            collecting = True
            toc_page_budget = 2
            toc_pages.add(page_no)
            lines = lines[1:]
        elif not collecting or toc_page_budget <= 0:
            continue
        elif raw and _looks_like_body_unit_start(lines, raw):
            collecting = False
            continue
        else:
            toc_pages.add(page_no)

        toc_page_budget -= 1
        index = 0
        while index < len(lines):
            line = lines[index]
            if pending_arabic is not None and _TOC_PAGE_NUM.match(line):
                name, title = pending_arabic
                raw.append(_TocEntry(name, title, int(line)))
                pending_arabic = None
                index += 1
                continue
            pending_arabic = None

            if _LONE_INDEX.match(line):
                pending_cn = line
                index += 1
                continue

            if pending_cn is not None:
                title, hint = _split_title_page(line)
                if _valid_toc_title(title):
                    raw.append(
                        _TocEntry(_CN_ORDINAL[pending_cn] + title, title, hint or 0)
                    )
                pending_cn = None
                index += 1
                continue

            arabic = _ARABIC_TOC_ENTRY.match(line)
            if arabic:
                number, title = arabic.group(1), re.sub(r"\s+", "", arabic.group(2))
                if _valid_toc_title(title) and number in _ARABIC_ORDINAL:
                    name = (
                        title
                        if title in _STANDALONE_TITLES or title.startswith("数学广角")
                        else _ARABIC_ORDINAL[number] + title
                    )
                    pending_arabic = (name, title)
                index += 1
                continue

            title, hint = _split_title_page(line)
            if title in _STANDALONE_TITLES or title.startswith("数学广角"):
                if _valid_toc_title(title):
                    raw.append(_TocEntry(title, title, hint or 0))
            index += 1

        if toc_page_budget <= 0:
            collecting = False

    return _validate_toc_entries(raw), toc_pages


def _looks_like_body_unit_start(lines: list[str], entries: list[_TocEntry]) -> bool:
    if not entries or not lines:
        return False
    first_title = entries[0].title
    if len(lines) >= 2 and (
        _LONE_INDEX.match(lines[0]) or _TOC_PAGE_NUM.match(lines[0])
    ):
        return re.sub(r"\s+", "", lines[1]) == first_title
    return re.sub(r"\s+", "", lines[0]) == first_title


def _split_title_page(line: str) -> tuple[str, int | None]:
    matched = _TITLE_WITH_PAGE.match(line)
    if matched:
        return re.sub(r"\s+", "", matched.group(1)), int(matched.group(2))
    return re.sub(r"\s+", "", line), None


def _valid_toc_title(title: str) -> bool:
    if not title or _WATERMARK in title:
        return False
    if not _HAS_CJK.search(title):
        return False
    if len(title) < 2 or len(title) > 24:
        return False
    if _NOISE_TITLE.search(title):
        return False
    if _TOC_PAGE_NUM.match(title) or _LONE_INDEX.match(title):
        return False
    return True


def _validate_toc_entries(entries: list[_TocEntry]) -> list[_TocEntry]:
    cleaned: list[_TocEntry] = []
    last_hint = -1
    seen_titles: set[str] = set()
    for entry in entries:
        if entry.title in seen_titles:
            continue
        if entry.page_hint and entry.page_hint < last_hint:
            continue
        seen_titles.add(entry.title)
        cleaned.append(entry)
        if entry.page_hint:
            last_hint = entry.page_hint
    return cleaned


def _spans_from_toc(
    pages: list[tuple[int, str]],
    toc_entries: list[_TocEntry],
    toc_pages: set[int],
) -> list[tuple[str, int, int, str]]:
    starts: list[tuple[str, int]] = []
    min_page = 1
    for entry in toc_entries:
        page = _find_body_start(pages, entry.title, toc_pages, min_page)
        if page is None:
            continue
        starts.append((entry.unit_name, page))
        min_page = page + 1
    if len(starts) < 2:
        return []
    spans: list[tuple[str, int, int, str]] = []
    last_page = pages[-1][0]
    for index, (unit_name, start) in enumerate(starts):
        end = starts[index + 1][1] - 1 if index + 1 < len(starts) else last_page
        body = [
            text.strip()
            for page_no, text in pages
            if page_no not in toc_pages and start <= page_no <= end
        ]
        spans.append((unit_name, start, end, "\n".join(body)))
    return spans


def _find_body_start(
    pages: list[tuple[int, str]],
    title: str,
    toc_pages: set[int],
    min_page: int,
) -> int | None:
    compact_title = re.sub(r"\s+", "", title)
    for page_no, text in pages:
        if page_no < min_page or page_no in toc_pages:
            continue
        lines = [raw.strip() for raw in text.splitlines() if raw.strip()]
        for index, line in enumerate(lines):
            compact = re.sub(r"\s+", "", line)
            if compact == compact_title:
                return page_no
            if (
                (_TOC_PAGE_NUM.match(line) or _LONE_INDEX.match(line))
                and index + 1 < len(lines)
                and re.sub(r"\s+", "", lines[index + 1]) == compact_title
            ):
                return page_no
    return None


def _spans_from_cn_headings(
    pages: list[tuple[int, str]],
    toc_pages: set[int],
) -> list[tuple[str, int, int, str]]:
    lines = _flat_body_lines(pages, toc_pages)
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
        heading, skip = _cn_heading_at(lines, index)
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


def _flat_body_lines(
    pages: list[tuple[int, str]],
    toc_pages: set[int],
) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for page_no, text in pages:
        if page_no in toc_pages:
            continue
        for raw in text.splitlines():
            line = raw.strip()
            if line and _WATERMARK not in line:
                lines.append((page_no, line))
    return lines


def _cn_title_usable(title: str) -> bool:
    if title.startswith("年") or len(title) < 4:
        return False
    if _WATERMARK in title or _TOC_PAGE_NUM.match(title):
        return False
    if _LONE_INDEX.match(title) or _NOISE_TITLE.search(title):
        return False
    if not _HAS_CJK.search(title):
        return False
    return True


def _cn_heading_at(lines: list[tuple[int, str]], index: int) -> tuple[str | None, int]:
    """Return (unit_name, lines_consumed) for 2022-style Chinese unit indexes."""
    _page_no, line = lines[index]
    if line in _STANDALONE_TITLES:
        return line, 1
    if line.startswith("数学广角") and len(line) <= 40:
        return re.sub(r"\s+", "", line), 1
    if _INLINE_UNIT.search(line) and len(line) <= 40:
        return re.sub(r"\s+", "", line), 1
    if _LONE_INDEX.match(line) and index + 1 < len(lines):
        title = lines[index + 1][1]
        if not _cn_title_usable(title):
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
