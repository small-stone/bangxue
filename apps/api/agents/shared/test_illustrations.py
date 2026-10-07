"""Unit tests for structured quiz illustrations."""

from __future__ import annotations

import pytest

from agents.shared.illustrations import (
    SceneValidationError,
    attach_illustration,
    count_items_in_svg,
    render_png,
    render_svg,
    svg_to_png,
    total_item_count,
    validate_scene,
)


def test_validate_scene_ok():
    scene = validate_scene(
        {"kind": "row_of_groups", "item": "fish", "groups": [{"count": 3}, {"count": 6}]}
    )
    assert scene["item"] == "fish"
    assert total_item_count(scene) == 9


@pytest.mark.parametrize(
    "raw",
    [
        {"kind": "freeform", "item": "fish", "groups": [{"count": 2}]},
        {"kind": "row_of_groups", "item": "fish", "groups": []},
        {"kind": "row_of_groups", "item": "fish", "groups": [{"count": 0}]},
        {"kind": "row_of_groups", "item": "fish", "groups": [{"count": 11}]},
        {"kind": "row_of_groups", "item": "!!!", "groups": [{"count": 2}]},
        None,
        "not-a-dict",
    ],
)
def test_validate_scene_rejects(raw):
    with pytest.raises(SceneValidationError):
        validate_scene(raw)


def test_render_svg_count_matches_schema():
    scene = {"kind": "row_of_groups", "item": "strawberry", "groups": [{"count": 6}]}
    svg = render_svg(scene)
    assert count_items_in_svg(svg) == 6
    assert 'class="count-item"' in svg


def test_render_svg_multi_group():
    scene = {
        "kind": "row_of_groups",
        "item": "fish",
        "groups": [{"count": 3}, {"count": 6}, {"count": 7}],
    }
    svg = render_svg(scene)
    assert count_items_in_svg(svg) == 16


def test_render_png_and_svg_to_png_nonempty():
    scene = {"kind": "row_of_groups", "item": "apple", "groups": [{"count": 4}, {"count": 2}]}
    png = render_png(scene)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png) > 100
    svg = render_svg(scene)
    png2 = svg_to_png(svg)
    assert png2[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(png2) > 100


def test_attach_illustration_ok_and_degrade():
    ok = attach_illustration(
        {
            "stem": "数一数",
            "scene": {"kind": "row_of_groups", "item": "fish", "groups": [{"count": 3}]},
        }
    )
    assert "illustration" in ok
    assert ok["illustration"]["scene"]["groups"][0]["count"] == 3
    assert count_items_in_svg(ok["illustration"]["svg"]) == 3

    bad = attach_illustration(
        {"stem": "纯文字", "scene": {"kind": "unknown", "groups": [{"count": 2}]}}
    )
    assert "illustration" not in bad
    assert bad["stem"] == "纯文字"
