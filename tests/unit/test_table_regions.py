# -*- coding: utf-8 -*-
"""S1 unit tests: component aggregation into TableRegion."""

from __future__ import annotations

from icpdf.parser.config import TableParams
from icpdf.parser.layout import PageLayout
from icpdf.parser.rule_primitives import RuleComponent, RuleSegment
from icpdf.parser.structure import recognize_structure
from icpdf.parser.table_regions import detect_table_regions
from icpdf.parser.text_blocks import TextBlock, TextSpan, TextWord


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


def test_caption_text_blocks_merge_even_at_body_size():
    """Font size is not the signal: a body-size caption still starts a table."""
    upper = _component(0, 240.0, 80.0, 400.0, 134.0)
    lower = _component(1, 240.0, 146.0, 400.0, 200.0)
    blocks = [
        _block("body-upper", [_span("s1", "value", (250.0, 90.0, 390.0, 99.0), 8.0)]),
        _block("body-lower", [_span("s2", "value", (250.0, 160.0, 390.0, 169.0), 8.0)]),
        _block("caption", [_span("s3", "Table 6-1. Independent table",
                                 (250.0, 136.0, 390.0, 145.0), 8.0)]),
    ]
    regions = detect_table_regions(_layout([upper, lower], blocks), TableParams())
    assert len(regions) == 2
    assert all(not region.evidence for region in regions)


def test_larger_section_heading_in_gap_still_merges():
    """An in-table section band may be set larger than the body text."""
    upper = _component(0, 240.0, 80.0, 400.0, 134.0)
    lower = _component(1, 240.0, 146.0, 400.0, 200.0)
    blocks = [
        _block("body-upper", [_span("s1", "value", (250.0, 90.0, 390.0, 99.0), 8.0)]),
        _block("body-lower", [_span("s2", "value", (250.0, 160.0, 390.0, 169.0), 8.0)]),
        _block("heading", [_span("s3", "Power Supply",
                                 (250.0, 136.0, 390.0, 145.0), 12.0)]),
    ]
    regions = detect_table_regions(_layout([upper, lower], blocks), TableParams())
    assert len(regions) == 1
    assert regions[0].components[0].component_id == 0
    assert regions[0].components[1].component_id == 1


def test_independent_tables_sharing_columns_do_not_merge():
    """Same lattice, same extent, 12pt gap, but captioned as two tables."""
    upper = _component(0, 240.0, 80.0, 400.0, 134.0)
    lower = _component(1, 240.0, 146.0, 400.0, 200.0)
    blocks = [
        _block("body-upper", [_span("s1", "value", (250.0, 90.0, 390.0, 99.0), 8.0)]),
        _block("body-lower", [_span("s2", "value", (250.0, 160.0, 390.0, 169.0), 8.0)]),
        _block("caption", [_span("s3", "Table 12. Configuration registers",
                                 (250.0, 136.0, 390.0, 145.0), 10.0)]),
    ]
    regions = detect_table_regions(_layout([upper, lower], blocks), TableParams())
    assert len(regions) == 2
    assert all(region.boundary_source == "ruled" for region in regions)


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


def test_section_local_column_does_not_split_other_sections():
    """A rule that exists in one section is a region column, but rows in
    sections without it merge across it instead of gaining empty cells."""
    upper = _component(0, 60.0, 80.0, 500.0, 134.0,
                       inner_xs=(240.0, 320.0, 400.0))
    lower = _component(1, 60.0, 146.0, 500.0, 200.0,
                       inner_xs=(240.0, 400.0))
    words = [
        TextWord(word_id="w1", text="alpha", bbox=(245.0, 86.0, 310.0, 94.0)),
        TextWord(word_id="w2", text="beta", bbox=(330.0, 86.0, 395.0, 94.0)),
        TextWord(word_id="w3", text="wide-value",
                 bbox=(245.0, 152.0, 395.0, 160.0)),
    ]
    layout = PageLayout(page_number=1, rect=(0.0, 0.0, 612.0, 792.0),
                        blocks=[], words=words, row_bands=[],
                        components=[upper, lower])
    regions = detect_table_regions(layout, TableParams())
    assert len(regions) == 1
    grid = recognize_structure(layout, regions[0])
    assert any(abs(x - 320.0) <= 2.5 for x in grid.xs)

    upper_band = [cell for cell in grid.cells if cell.row == 0]
    assert any(abs(cell.column_span - 1) == 0 and cell.column == 1
               for cell in upper_band)
    assert any(cell.column == 2 and cell.column_span == 1
               for cell in upper_band)

    lower_band = [cell for cell in grid.cells if cell.row == 4]
    assert not any(cell.column == 2 for cell in lower_band)
    assert any(cell.column == 1 and cell.column_span == 2
               for cell in lower_band)
