"""Layer 2 - table region detection.

Proposes table regions from evidence, without deciding structure or semantics.
Ruled pages use vector-rule components only.  On pages with no ruling at all, a
strict baseline-alignment fallback keeps text-only tables (including the
synthetic fixtures) working.  Text-alignment candidates are deliberately not
proposed on ruled pages: that was the source of the Phase 1.1 over-detection.
"""

from __future__ import annotations

import statistics

from icpdf.domain.common import BBox
from icpdf.parser.config import TableParams
from icpdf.parser.layout import PageLayout, RuleComponent
from icpdf.parser.structure import TableRegion
from icpdf.parser.text_blocks import TextWord


def _bbox_union(boxes: list[BBox]) -> BBox:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _group_cells(words: list[TextWord], gap: float) -> list[list[TextWord]]:
    ordered = sorted(words, key=lambda w: w.bbox[0])
    groups: list[list[TextWord]] = []
    for word in ordered:
        if groups and word.bbox[0] - max(w.bbox[2] for w in groups[-1]) <= gap:
            groups[-1].append(word)
        else:
            groups.append([word])
    return groups


def _can_extend(current: list[list[TextWord]], words: list[TextWord],
                cells: list[list[TextWord]], last_bottom: float,
                median_h: float, params: TableParams) -> bool:
    modal = statistics.mode(len(row) for row in current) if current else len(cells)
    if abs(len(cells) - modal) > params.column_tolerance or len(cells) < 2:
        return False
    rows_box = _bbox_union([_bbox_union([w.bbox for w in row]) for row in current])
    row_box = _bbox_union([w.bbox for w in words])
    overlap = min(rows_box[2], row_box[2]) - max(rows_box[0], row_box[0])
    if overlap <= 0:
        return False
    return row_box[1] - last_bottom <= params.row_gap_factor * median_h


def _alignment_regions(layout: PageLayout, params: TableParams) -> list[TableRegion]:
    if not layout.row_bands:
        return []
    heights = [w.bbox[3] - w.bbox[1] for row in layout.row_bands for w in row
               if w.bbox[3] > w.bbox[1]]
    median_h = statistics.median(heights) if heights else 10.0
    regions: list[TableRegion] = []
    current: list[list[TextWord]] = []
    last_bottom = 0.0

    def close() -> None:
        nonlocal current
        if len(current) >= params.alignment_min_rows:
            rows = tuple(tuple(row) for row in current)
            bbox = _bbox_union([_bbox_union([w.bbox for w in row]) for row in current])
            regions.append(TableRegion(layout.page_number, bbox, "text_alignment",
                                       rows_words=rows))
        current = []

    for words in layout.row_bands:
        cells = _group_cells(words, params.cell_gap_pt)
        row_bbox = _bbox_union([w.bbox for w in words])
        if any(len(" ".join(w.text for w in cell)) > params.max_cell_chars
               for cell in cells):
            close()
            last_bottom = row_bbox[3]
            continue
        if len(cells) < 2:
            close()
            last_bottom = row_bbox[3]
            continue
        if current and not _can_extend(current, words, cells, last_bottom,
                                       median_h, params):
            close()
        current.append(words)
        last_bottom = row_bbox[3]
    close()
    return regions


def _component_region(layout: PageLayout, component: RuleComponent) -> TableRegion:
    return TableRegion(layout.page_number, component.bbox, "rule_lattice",
                       component=component)


def detect_table_regions(layout: PageLayout,
                         params: TableParams | None = None) -> list[TableRegion]:
    params = params or TableParams()
    regions = [_component_region(layout, component) for component in layout.components]
    if not layout.components:
        regions.extend(_alignment_regions(layout, params))
    regions.sort(key=lambda region: (round(region.bbox[1], 1), round(region.bbox[0], 1)))
    return regions


__all__ = ["detect_table_regions"]
