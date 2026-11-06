# -*- coding: utf-8 -*-
"""S1 unit tests: component aggregation into TableRegion."""

from __future__ import annotations

from icpdf.parser.config import TableParams
from icpdf.parser.layout import PageLayout
from icpdf.parser.rule_primitives import RuleComponent, RuleSegment
from icpdf.parser.table_regions import detect_table_regions
from icpdf.parser.text_blocks import TextBlock, TextSpan


def _component(component_id: int, x0: float, y0: float, x1: float, y1: float,
               inner_xs: tuple[float, ...] = (240.0, 400.0),
               extent: tuple[float, float] = (60.0, 500.0),
               rows: int = 3) -> RuleComponent:
    ys = [y0 + index * ((y1 - y0) / rows) for index in range(rows + 1)]
    horizontal = tuple(RuleSegment("h", extent[0], extent[1], y) for y in ys)
    vertical = tuple(RuleSegment("v", y0, y1, x) for x in inner_xs)
    return RuleComponent((x0, y0, x1, y1), horizontal, vertical,
                         page_number=1, component_id=component_id)


def _span(span_id: str, text: str, bbox: tuple[float, float, float, float],
          size: float) -> TextSpan:
    return TextSpan(span_id=span_id, bbox=bbox, text=text, font="Helvetica",
                    size=size)


def _block(block_id: str, spans: list[TextSpan]) -> TextBlock:
    return TextBlock(block_id=block_id, page_number=1,
                     bbox=(min(s.bbox[0] for s in spans),
                           min(s.bbox[1] for s in spans),
                           max(s.bbox[2] for s in spans),
                           max(s.bbox[3] for s in spans)),
                     spans=spans)


def _layout(components: list[RuleComponent],
            blocks: list[TextBlock] | None = None) -> PageLayout:
    return PageLayout(page_number=1, rect=(0.0, 0.0, 612.0, 792.0),
                      blocks=blocks or [], words=[], row_bands=[],
                      components=components)


def test_stacked_components_merge_into_one_region():
    upper = _component(0, 240.0, 80.0, 400.0, 134.0)
    lower = _component(1, 240.0, 146.0, 400.0, 200.0)
    regions = detect_table_regions(_layout([upper, lower]), TableParams())

    assert len(regions) == 1
    region = regions[0]
    assert [component.component_id for component in region.components] == [0, 1]
    assert region.bbox == (60.0, 80.0, 500.0, 200.0)
    assert region.boundary_source == "implied_horizontal"
    kinds = [item.kind for item in region.evidence]
    assert "merge" in kinds and "absorbed" in kinds and "implied_outer" in kinds
    assert region.component is not None and region.component.component_id == -1
    assert len(region.component.horizontal) == 8


def test_absorbed_component_is_not_emitted_separately():
    upper = _component(0, 240.0, 80.0, 400.0, 134.0)
    lower = _component(1, 240.0, 146.0, 400.0, 200.0)
    regions = detect_table_regions(_layout([upper, lower]), TableParams())
    assert len(regions) == 1
    absorbed = [item for item in regions[0].evidence if item.kind == "absorbed"]
    assert len(absorbed) == 1
    assert absorbed[0].component_ids == (1,)


def test_caption_sized_gap_blocks_merge():
    upper = _component(0, 240.0, 80.0, 400.0, 134.0)
    lower = _component(1, 240.0, 146.0, 400.0, 200.0)
    blocks = [
        _block("body-upper", [_span("s1", "value", (250.0, 90.0, 390.0, 99.0), 8.0)]),
        _block("body-lower", [_span("s2", "value", (250.0, 160.0, 390.0, 169.0), 8.0)]),
        _block("caption", [_span("s3", "Table 6-1", (250.0, 136.0, 390.0, 145.0), 10.0)]),
    ]
    regions = detect_table_regions(_layout([upper, lower], blocks), TableParams())
    assert len(regions) == 2
    assert all(not region.evidence for region in regions)


def test_dissimilar_column_lattices_stay_separate():
    upper = _component(0, 240.0, 80.0, 400.0, 134.0)
    lower = _component(1, 300.0, 146.0, 450.0, 200.0,
                       inner_xs=(300.0, 450.0))
    regions = detect_table_regions(_layout([upper, lower]), TableParams())
    assert len(regions) == 2


def test_touching_components_are_not_merged():
    upper = _component(0, 240.0, 80.0, 400.0, 134.0)
    lower = _component(1, 240.0, 134.0, 400.0, 200.0)
    regions = detect_table_regions(_layout([upper, lower]), TableParams())
    assert len(regions) == 2


def test_single_component_keeps_ruled_boundary():
    only = _component(0, 240.0, 80.0, 400.0, 200.0)
    regions = detect_table_regions(_layout([only]), TableParams())
    assert len(regions) == 1
    assert regions[0].boundary_source == "ruled"
    assert regions[0].evidence == ()
