"""Split extracted pages on textbook unit headings."""

import re
from dataclasses import dataclass

# "第一单元 …" or "第 1 单元 …" on one line.
_INLINE_UNIT = re.compile(
    r"第\s*[0-9０-９一二三四五六七八九十百零〇]+\s*单\s*元"
)
# English primary books: "Unit 1 Making friends 2" (TOC) / "Unit 1" (body).
_EN_UNIT_TOC = re.compile(
    r"^Unit\s+(\d{1,2})\s+(.+?)(?:\s+(\d{1,3}))?\s*$",
    re.IGNORECASE,
)
# Older PEP English TOC: "2 Unit 1 My day"
_EN_UNIT_TOC_PAGE_FIRST = re.compile(
    r"^(\d{1,3})\s+Unit\s+(\d{1,2})\s+(.+)$",
    re.IGNORECASE,
)
_EN_UNIT_HEADING = re.compile(r"^Unit\s+(\d{1,2})\b(.*)$", re.IGNORECASE)
_EN_UNIT_WORD_HEADING = re.compile(
    r"^Unit\s+(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)\b(.*)$",
    re.IGNORECASE,
)
_EN_UNIT_WORD_TO_NUM = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
}
# Chinese language arts TOC: "第一单元·识字" / "第一单元 1"
_CN_UNIT_TOC = re.compile(
    r"第([一二三四五六七八九十]+)单元(?:[·•．.]([^\d◎]{1,12}))?(?:\s+(\d{1,3}))?"
)
# Two-column Chinese TOC after whitespace collapse: "第一单元1第三单元27"
_CN_UNIT_WITH_PAGE = re.compile(
    r"第([一二三四五六七八九十]+)单元(?:[·•．.][^\d第]{0,12})?[^\d第]{0,40}?(\d{1,3})"
)
# Grade-1 style subtitle on the same heading: "第一单元·识字"
_CN_UNIT_WITH_THEME = re.compile(
    r"第([一二三四五六七八九十]+)单元[·•．.]([^\d第]{1,8})"
)
_CN_KNOWN_THEMES = ("汉语拼音", "识字", "阅读", "习作")
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
    candidates: list[list[tuple[str, int, int, str]]] = []
    if len(toc_entries) >= 2:
        toc_spans = _spans_from_toc(pages, toc_entries, toc_pages)
        if toc_spans:
            candidates.append(toc_spans)
    cn = _spans_from_cn_headings(pages, toc_pages)
    if cn:
        candidates.append(cn)
    en = _spans_from_en_headings(pages, toc_pages)
    if en:
        candidates.append(en)
    if candidates:
        best = max(
            candidates,
            key=lambda item: (
                _span_coverage(item, pages),
                len(item),
            ),
        )
        if _span_coverage(best, pages) >= 0.3 and len(best) >= 2:
            return best
        if _span_coverage(best, pages) >= 0.3:
            return best
    return _spans_whole_book(pages, toc_pages)


def _spans_whole_book(
    pages: list[tuple[int, str]],
    toc_pages: set[int],
) -> list[tuple[str, int, int, str]]:
    """Fallback so OCR-hostile books still enter the RAG store."""
    body = [(page_no, text) for page_no, text in pages if page_no not in toc_pages]
    if not body:
        body = pages
    if not body:
        return []
    text = "\n".join(chunk for _page_no, chunk in body)
    return [("全文", body[0][0], body[-1][0], text)]


def _span_coverage(
    spans: list[tuple[str, int, int, str]],
    pages: list[tuple[int, str]],
) -> float:
    if not spans or not pages:
        return 0.0
    covered = sum(max(0, end - start + 1) for _name, start, end, _text in spans)
    return covered / max(1, pages[-1][0])


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
        first_lower = lines[0].strip().lower()
        if first in {"目录", "目錄"} or first_lower == "contents":
            collecting = True
            # English Contents is usually one page; Chinese TOC often spans 2–3.
            toc_page_budget = 1 if first_lower == "contents" else 3
            toc_pages.add(page_no)
            lines = lines[1:]
        elif not collecting or toc_page_budget <= 0:
            continue
        elif raw and (
            _looks_like_body_unit_start(lines, raw) or not _page_has_toc_signal(lines)
        ):
            collecting = False
            continue
        else:
            toc_pages.add(page_no)

        toc_page_budget -= 1
        page_added = False

        # Prefer whole-page Chinese unit+page extraction (handles two-column TOC).
        cn_page_entries = _extract_cn_units_from_toc_page(text)
        if cn_page_entries:
            raw.extend(cn_page_entries)
            page_added = True

        index = 0
        while index < len(lines):
            line = lines[index]
            if pending_arabic is not None and _TOC_PAGE_NUM.match(line):
                name, title = pending_arabic
                raw.append(_TocEntry(name, title, int(line)))
                pending_arabic = None
                page_added = True
                index += 1
                continue
            pending_arabic = None

            en_page_first = _EN_UNIT_TOC_PAGE_FIRST.match(line)
            if en_page_first:
                hint = int(en_page_first.group(1))
                number = en_page_first.group(2)
                title = en_page_first.group(3).strip()
                if _valid_en_toc_title(title):
                    unit_name = f"Unit {number} {title}".strip()
                    raw.append(_TocEntry(unit_name, title, hint))
                    page_added = True
                index += 1
                continue

            en_toc = _EN_UNIT_TOC.match(line)
            if en_toc:
                number, title = en_toc.group(1), en_toc.group(2).strip()
                hint = int(en_toc.group(3)) if en_toc.group(3) else 0
                if _valid_en_toc_title(title):
                    unit_name = f"Unit {number} {title}".strip()
                    raw.append(_TocEntry(unit_name, title, hint))
                    page_added = True
                index += 1
                continue

            # Skip per-line Chinese unit parsing when page-level extract already ran.
            if cn_page_entries:
                index += 1
                continue

            if _LONE_INDEX.match(line):
                pending_cn = line
                index += 1
                continue

            if pending_cn is not None:
                title, hint = _split_title_page(line)
                if _valid_toc_title(title) and len(title) <= 12 and "，" not in title:
                    raw.append(
                        _TocEntry(_CN_ORDINAL[pending_cn] + title, title, hint or 0)
                    )
                    page_added = True
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
                    page_added = True
            index += 1

        if not page_added and page_no in toc_pages and page_no != min(toc_pages):
            # Drop trailing non-TOC pages that were only claimed by budget.
            toc_pages.discard(page_no)
            collecting = False
        if toc_page_budget <= 0:
            collecting = False

    return _validate_toc_entries(raw), toc_pages


def _extract_cn_units_from_toc_page(text: str) -> list[_TocEntry]:
    """Pull 第N单元 + printed page from a (possibly two-column) TOC page."""
    compact = re.sub(r"\s+", "", text).replace(_WATERMARK, "")
    starts = list(re.finditer(r"第([一二三四五六七八九十]+)单元", compact))
    if not starts:
        return []
    by_ordinal: dict[str, _TocEntry] = {}
    for index, match in enumerate(starts):
        ordinal = match.group(1)
        end = (
            starts[index + 1].start()
            if index + 1 < len(starts)
            else min(len(compact), match.end() + 48)
        )
        window = compact[match.start() : end]
        theme = _cn_theme_from_window(window)
        numbers = [int(num) for num in re.findall(r"\d{1,3}", window)]
        unit_name = f"第{ordinal}单元" + (f"·{theme}" if theme else "")
        title = theme or unit_name
        if not numbers:
            if theme or ordinal:
                by_ordinal.setdefault(ordinal, _TocEntry(unit_name, title, 0))
            continue
        # "第一单元·识字1天地人8" → lesson index then page; use the page.
        hint = numbers[1] if theme and len(numbers) > 1 else numbers[0]
        if hint > 160:
            continue
        prev = by_ordinal.get(ordinal)
        if prev is None or (hint and (not prev.page_hint or hint < prev.page_hint)):
            by_ordinal[ordinal] = _TocEntry(unit_name, title, hint)
    order = "一二三四五六七八九十"
    return [
        by_ordinal[key]
        for key in sorted(by_ordinal.keys(), key=lambda item: order.find(item))
        if key in by_ordinal
    ]


def _page_has_toc_signal(lines: list[str]) -> bool:
    for index, line in enumerate(lines):
        compact = re.sub(r"\s+", "", line)
        if _EN_UNIT_TOC.match(line) or _EN_UNIT_TOC_PAGE_FIRST.match(line):
            return True
        if _CN_UNIT_TOC.search(line) or _CN_UNIT_TOC.search(compact):
            return True
        if _ARABIC_TOC_ENTRY.match(line):
            return True
        if _LONE_INDEX.match(line) and index + 1 < len(lines):
            title, _hint = _split_title_page(lines[index + 1])
            if _valid_toc_title(title) and len(title) <= 12:
                return True
    return False


def _cn_theme_from_window(window: str) -> str:
    theme_match = _CN_UNIT_WITH_THEME.match(window)
    if not theme_match:
        return ""
    raw = theme_match.group(2)
    for known in _CN_KNOWN_THEMES:
        if raw.startswith(known):
            return known
    if _valid_toc_title(raw) and len(raw) <= 4:
        return raw
    return ""


def _peek_following_page_hint(lines: list[str], start: int) -> int:
    for line in lines[start : start + 8]:
        _title, hint = _split_title_page(line)
        if hint:
            return hint
        if _TOC_PAGE_NUM.match(line):
            return int(line)
    return 0


def _looks_like_body_unit_start(lines: list[str], entries: list[_TocEntry]) -> bool:
    if not entries or not lines:
        return False
    first_title = re.sub(r"\s+", "", entries[0].title)
    first_unit = entries[0].unit_name
    if _EN_UNIT_HEADING.match(lines[0]):
        compact0 = re.sub(r"\s+", "", lines[0])
        if first_title and first_title in compact0:
            return True
        if re.sub(r"\s+", "", first_unit) in compact0:
            return True
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


def _valid_en_toc_title(title: str) -> bool:
    cleaned = title.strip()
    if not cleaned or _WATERMARK in cleaned:
        return False
    if len(cleaned) < 2 or len(cleaned) > 60:
        return False
    if _TOC_PAGE_NUM.match(cleaned):
        return False
    return bool(re.search(r"[A-Za-z]", cleaned))


def _validate_toc_entries(entries: list[_TocEntry]) -> list[_TocEntry]:
    cleaned: list[_TocEntry] = []
    last_hint = -1
    seen_units: set[str] = set()
    for entry in entries:
        # Titles like "汉语拼音" / "阅读" repeat across units; key on unit_name.
        if entry.unit_name in seen_units:
            continue
        # OCR sometimes glues digits into absurd page hints (e.g. 692).
        if entry.page_hint > 160:
            continue
        if entry.page_hint and entry.page_hint < last_hint:
            continue
        seen_units.add(entry.unit_name)
        cleaned.append(entry)
        if entry.page_hint:
            last_hint = entry.page_hint
    return cleaned


def _spans_from_toc(
    pages: list[tuple[int, str]],
    toc_entries: list[_TocEntry],
    toc_pages: set[int],
) -> list[tuple[str, int, int, str]]:
    offset = _estimate_page_offset(pages, toc_entries, toc_pages)
    starts: list[tuple[str, int]] = []
    min_page = 1
    last_page = pages[-1][0]
    body_start = (max(toc_pages) + 1) if toc_pages else 1
    for entry in toc_entries:
        page = None
        # Prefer printed-page mapping when OCR body titles are unreliable.
        if offset is not None and entry.page_hint:
            mapped = entry.page_hint + offset
            if (
                mapped >= min_page
                and mapped <= last_page
                and mapped not in toc_pages
            ):
                page = mapped
        elif offset is not None and not entry.page_hint and not starts:
            page = max(min_page, body_start)
        if page is None:
            page = _find_body_start(pages, entry, toc_pages, min_page)
        if page is None or page > last_page:
            continue
        starts.append((entry.unit_name, page))
        min_page = page + 1
    if len(starts) < 2:
        return []
    spans: list[tuple[str, int, int, str]] = []
    for index, (unit_name, start) in enumerate(starts):
        end = starts[index + 1][1] - 1 if index + 1 < len(starts) else last_page
        if end < start:
            continue
        body = [
            text.strip()
            for page_no, text in pages
            if page_no not in toc_pages and start <= page_no <= end
        ]
        spans.append((unit_name, start, end, "\n".join(body)))
    return spans


def _estimate_page_offset(
    pages: list[tuple[int, str]],
    toc_entries: list[_TocEntry],
    toc_pages: set[int],
) -> int | None:
    """Map printed page numbers from the TOC onto PDF page indexes."""
    first_hint = next((e.page_hint for e in toc_entries if e.page_hint), 0)
    footer_offset = None
    if first_hint:
        for page_no, text in pages:
            if page_no in toc_pages:
                continue
            lines = [
                raw.strip()
                for raw in text.splitlines()
                if raw.strip() and _WATERMARK not in raw
            ]
            if not lines:
                continue
            # Printed page numbers usually sit alone near the end of the page.
            for candidate in lines[-4:]:
                if _TOC_PAGE_NUM.match(candidate) and int(candidate) == first_hint:
                    footer_offset = page_no - first_hint
                    break
            if footer_offset is not None:
                break
    if footer_offset is not None and 0 <= footer_offset <= 20:
        return footer_offset
    for entry in toc_entries:
        if not entry.page_hint:
            continue
        found = _find_body_start(pages, entry, toc_pages, 1)
        if found is None:
            continue
        offset = found - entry.page_hint
        # Title matches in appendices can explode the offset; ignore those.
        if 0 <= offset <= 20:
            return offset
    return footer_offset if footer_offset is not None and footer_offset >= 0 else None


def _find_body_start(
    pages: list[tuple[int, str]],
    entry: _TocEntry,
    toc_pages: set[int],
    min_page: int,
) -> int | None:
    title = entry.title
    compact_title = re.sub(r"\s+", "", title)
    unit_compact = re.sub(r"\s+", "", entry.unit_name)
    for page_no, text in pages:
        if page_no < min_page or page_no in toc_pages:
            continue
        lines = [raw.strip() for raw in text.splitlines() if raw.strip()]
        for index, line in enumerate(lines):
            compact = re.sub(r"\s+", "", line)
            if compact_title and compact == compact_title:
                return page_no
            if unit_compact.startswith("第") and compact.startswith(unit_compact[:4]):
                # "第一单元·识字" or body "第一单元"
                if compact == unit_compact or compact.startswith(
                    re.sub(r"·.*$", "", unit_compact)
                ):
                    return page_no
            en = _EN_UNIT_HEADING.match(line)
            word = _EN_UNIT_WORD_HEADING.match(line)
            if en and compact_title and compact_title.lower() in compact.lower():
                return page_no
            if word and compact_title:
                next_compact = (
                    re.sub(r"\s+", "", lines[index + 1])
                    if index + 1 < len(lines)
                    else ""
                )
                if compact_title.lower() in compact.lower() or next_compact.lower() == compact_title.lower():
                    return page_no
            if (
                (_TOC_PAGE_NUM.match(line) or _LONE_INDEX.match(line))
                and index + 1 < len(lines)
                and re.sub(r"\s+", "", lines[index + 1]) == compact_title
            ):
                return page_no
            if en and index + 1 < len(lines):
                next_compact = re.sub(r"\s+", "", lines[index + 1])
                if next_compact.lower() == compact_title.lower():
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


def _spans_from_en_headings(
    pages: list[tuple[int, str]],
    toc_pages: set[int],
) -> list[tuple[str, int, int, str]]:
    """Split on English 'Unit N …' body headings when TOC mapping is weak."""
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

    for page_no, line in lines:
        matched = _EN_UNIT_HEADING.match(line)
        word = _EN_UNIT_WORD_HEADING.match(line)
        heading = None
        if matched and _clean_en_heading(line, matched.group(2) or ""):
            number = matched.group(1)
            rest = (matched.group(2) or "").strip(" .-–—")
            heading = f"Unit {number} {rest}".strip() if rest else f"Unit {number}"
        elif word and _clean_en_heading(line, word.group(2) or ""):
            number = _EN_UNIT_WORD_TO_NUM[word.group(1).lower()]
            rest = (word.group(2) or "").strip(" .-–—")
            heading = f"Unit {number} {rest}".strip() if rest else f"Unit {number}"
        if heading is not None:
            flush()
            current_name = heading
            current_start = page_no
            current_end = page_no
            current_lines = [heading]
            continue
        if current_name is not None:
            current_end = page_no
            current_lines.append(line)
    flush()
    return spans


def _clean_en_heading(line: str, rest: str) -> bool:
    """Reject glossary / vocabulary noise that only mentions Unit N."""
    if len(line) > 60:
        return False
    if re.search(r"[/\\]|\bp\.\s*\d|需要|听听|词汇", line):
        return False
    if rest.count("Unit") >= 1:
        return False
    return True


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
