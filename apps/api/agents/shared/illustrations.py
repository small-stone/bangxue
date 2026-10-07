"""Structured quiz scene validation and deterministic illustration rendering.

Phase-1 scene kind: row_of_groups — horizontal containers with countable items.
No text-to-image APIs; counts are guaranteed by the renderer.
"""

from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from typing import Any

from PIL import Image, ImageDraw

MIN_ITEM_COUNT = 1
MAX_ITEM_COUNT = 10
MAX_GROUPS = 8

ALLOWED_KINDS = frozenset({"row_of_groups"})
# Unknown item labels fall back to a generic circle glyph.
KNOWN_ITEMS = frozenset(
    {
        "fish",
        "strawberry",
        "apple",
        "star",
        "circle",
        "ball",
        "flower",
        "bird",
        "cat",
        "dog",
    }
)

ITEM_COLORS = {
    "fish": (56, 132, 196),
    "strawberry": (220, 68, 80),
    "apple": (210, 60, 60),
    "star": (230, 170, 40),
    "circle": (90, 120, 180),
    "ball": (70, 160, 90),
    "flower": (200, 100, 160),
    "bird": (80, 150, 200),
    "cat": (160, 120, 90),
    "dog": (140, 100, 70),
}


class SceneValidationError(ValueError):
    """Scene JSON failed structural validation."""


def validate_scene(raw: Any) -> dict[str, Any]:
    """Return a normalized scene dict or raise SceneValidationError."""
    if not isinstance(raw, dict):
        raise SceneValidationError("scene must be an object")

    kind = str(raw.get("kind") or "").strip()
    if kind not in ALLOWED_KINDS:
        raise SceneValidationError(f"unsupported scene kind: {kind!r}")

    item = str(raw.get("item") or "circle").strip().lower() or "circle"
    if not re.fullmatch(r"[a-z_]{1,32}", item):
        raise SceneValidationError(f"invalid item label: {item!r}")

    groups_raw = raw.get("groups")
    if not isinstance(groups_raw, list) or not groups_raw:
        raise SceneValidationError("scene.groups must be a non-empty list")
    if len(groups_raw) > MAX_GROUPS:
        raise SceneValidationError(f"too many groups (max {MAX_GROUPS})")

    groups: list[dict[str, int]] = []
    for index, group in enumerate(groups_raw):
        if not isinstance(group, dict):
            raise SceneValidationError(f"groups[{index}] must be an object")
        try:
            count = int(group.get("count"))
        except (TypeError, ValueError) as exc:
            raise SceneValidationError(f"groups[{index}].count must be an integer") from exc
        if count < MIN_ITEM_COUNT or count > MAX_ITEM_COUNT:
            raise SceneValidationError(
                f"groups[{index}].count must be in [{MIN_ITEM_COUNT}, {MAX_ITEM_COUNT}]"
            )
        groups.append({"count": count})

    return {"kind": kind, "item": item, "groups": groups}


def total_item_count(scene: dict[str, Any]) -> int:
    return sum(int(g["count"]) for g in scene["groups"])


def render_svg(scene: dict[str, Any]) -> str:
    """Build an SVG string with one `.count-item` node per declared object."""
    scene = validate_scene(scene)
    groups = scene["groups"]
    item = scene["item"]
    n_groups = len(groups)
    group_w = 88
    group_h = 96
    gap = 16
    pad = 12
    width = pad * 2 + n_groups * group_w + max(0, n_groups - 1) * gap
    height = pad * 2 + group_h + 20

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" data-kind="{scene["kind"]}" '
        f'data-item="{item}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fffaf2"/>',
    ]

    for gi, group in enumerate(groups):
        gx = pad + gi * (group_w + gap)
        gy = pad
        parts.append(
            f'<g class="group" data-group-index="{gi}" data-count="{group["count"]}">'
            f'<rect x="{gx}" y="{gy}" width="{group_w}" height="{group_h}" rx="10" '
            f'fill="#f3e6d4" stroke="#c4a574" stroke-width="2"/>'
        )
        count = group["count"]
        cols = min(count, 3) if count else 1
        rows = (count + cols - 1) // cols if count else 1
        for ii in range(count):
            row, col = divmod(ii, cols)
            cx = gx + group_w / 2 + (col - (cols - 1) / 2) * 22
            cy = gy + 28 + row * 22
            parts.append(_svg_item(item, cx, cy, ii))
        parts.append("</g>")

    parts.append("</svg>")
    return "".join(parts)


def _svg_item(item: str, cx: float, cy: float, index: int) -> str:
    color = {
        "fish": "#3884c4",
        "strawberry": "#dc4450",
        "apple": "#d23c3c",
        "star": "#e6aa28",
        "ball": "#46a05a",
        "flower": "#c864a0",
    }.get(item, "#5a78b4")
    # Each countable object is marked with class="count-item" for tests.
    if item == "star":
        return (
            f'<polygon class="count-item" data-item="{item}" data-index="{index}" '
            f'points="{cx},{cy - 8} {cx + 2.5},{cy - 2.5} {cx + 8},{cy - 2} '
            f'{cx + 3.5},{cy + 2} {cx + 5},{cy + 8} {cx},{cy + 4.5} '
            f'{cx - 5},{cy + 8} {cx - 3.5},{cy + 2} {cx - 8},{cy - 2} '
            f'{cx - 2.5},{cy - 2.5}" fill="{color}"/>'
        )
    return (
        f'<circle class="count-item" data-item="{item}" data-index="{index}" '
        f'cx="{cx:.1f}" cy="{cy:.1f}" r="7" fill="{color}"/>'
    )


def count_items_in_svg(svg: str) -> int:
    """Count `.count-item` nodes in an SVG string."""
    root = ET.fromstring(svg)
    return sum(1 for el in root.iter() if el.attrib.get("class") == "count-item")


def render_png(scene: dict[str, Any], *, scale: int = 2) -> bytes:
    """Rasterize the same scene layout to PNG bytes for PDF embedding."""
    scene = validate_scene(scene)
    groups = scene["groups"]
    item = scene["item"]
    n_groups = len(groups)
    group_w = 88
    group_h = 96
    gap = 16
    pad = 12
    width = pad * 2 + n_groups * group_w + max(0, n_groups - 1) * gap
    height = pad * 2 + group_h + 20
    img = Image.new("RGB", (width * scale, height * scale), (255, 250, 242))
    draw = ImageDraw.Draw(img)
    color = ITEM_COLORS.get(item, (90, 120, 180))

    def s(v: float) -> int:
        return int(round(v * scale))

    for gi, group in enumerate(groups):
        gx = pad + gi * (group_w + gap)
        gy = pad
        draw.rounded_rectangle(
            [s(gx), s(gy), s(gx + group_w), s(gy + group_h)],
            radius=s(10),
            fill=(243, 230, 212),
            outline=(196, 165, 116),
            width=max(1, scale),
        )
        count = group["count"]
        cols = min(count, 3) if count else 1
        for ii in range(count):
            row, col = divmod(ii, cols)
            cx = gx + group_w / 2 + (col - (cols - 1) / 2) * 22
            cy = gy + 28 + row * 22
            r = 7
            draw.ellipse(
                [s(cx - r), s(cy - r), s(cx + r), s(cy + r)],
                fill=color,
            )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def svg_to_png(svg: str, *, scale: int = 2) -> bytes:
    """Produce PNG for PDF. Prefer scene re-render when data-attrs are present.

    Falls back to parsing counts from the SVG and drawing a matching row so
    PDF embedding never depends on Cairo / text-to-image.
    """
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:
        raise SceneValidationError("invalid SVG") from exc

    kind = root.attrib.get("data-kind") or "row_of_groups"
    item = root.attrib.get("data-item") or "circle"
    groups: list[dict[str, int]] = []
    for el in root.iter():
        if el.attrib.get("class") == "group" and "data-count" in el.attrib:
            groups.append({"count": int(el.attrib["data-count"])})
    if not groups:
        # Reconstruct from count-item nodes as a single group.
        n = count_items_in_svg(svg)
        if n < MIN_ITEM_COUNT:
            raise SceneValidationError("SVG has no countable items")
        groups = [{"count": min(n, MAX_ITEM_COUNT)}]
    return render_png({"kind": kind, "item": item, "groups": groups}, scale=scale)


def attach_illustration(question: dict[str, Any]) -> dict[str, Any]:
    """Validate optional scene on a question and attach illustration.svg.

    On failure, drop the scene/illustration without raising (caller keeps stem).
    """
    raw_scene = question.pop("scene", None)
    if raw_scene is None:
        return question
    try:
        scene = validate_scene(raw_scene)
        svg = render_svg(scene)
        if count_items_in_svg(svg) != total_item_count(scene):
            return question
        question["illustration"] = {"scene": scene, "svg": svg}
    except (SceneValidationError, ET.ParseError, TypeError, ValueError):
        return question
    return question
