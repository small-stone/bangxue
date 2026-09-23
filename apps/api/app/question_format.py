"""Normalize and format quiz question fields for UI and PDF."""

from __future__ import annotations

_LETTERS = "ABCDEFGH"


def normalize_options(raw) -> list[str] | None:
    """Return labeled options like ['A. …', 'B. …'] or None."""
    if raw is None:
        return None

    texts: list[str] = []
    if isinstance(raw, dict):
        for key in sorted(raw.keys(), key=lambda k: str(k)):
            text = str(raw[key]).strip()
            if text:
                texts.append(_with_letter(str(key), text, len(texts)))
    elif isinstance(raw, list):
        for index, item in enumerate(raw):
            text = str(item).strip()
            if text:
                texts.append(_with_letter(None, text, index))
    else:
        return None
    return texts or None


def _with_letter(key: str | None, text: str, index: int) -> str:
    if len(text) >= 2 and text[0].upper() in _LETTERS and text[1] in ".、．":
        body = text[2:].strip()
        return f"{text[0].upper()}. {body}"
    letter = key.strip().upper().rstrip(".、．") if key else _LETTERS[index]
    if letter not in _LETTERS:
        letter = _LETTERS[index] if index < len(_LETTERS) else str(index + 1)
    return f"{letter}. {text}"


def format_question_body(item: dict, *, include_answer: bool = False) -> str:
    """Build multi-line text: stem, options, optional answer."""
    lines = [str(item.get("stem", "")).strip()]
    for option in item.get("options") or []:
        lines.append(str(option))
    if include_answer:
        answer = str(item.get("answer", "")).strip()
        if answer:
            lines.append(f"答案：{answer}")
    return "\n".join(line for line in lines if line)
