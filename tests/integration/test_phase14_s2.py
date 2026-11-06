# -*- coding: utf-8 -*-
"""S2a integration tests: the visual boundary lattice on the frozen PDFs.

The PDFs live outside the repository; the tests skip when they are absent.
Gold bboxes come from the frozen Gold v2 file, never from parser output.
"""

from __future__ import annotations

import json
from pathlib import Path

import pymupdf as fitz
import pytest
import yaml

from icpdf.parser.config import TableParams
from icpdf.parser.pdf_loader import load_pdf
from icpdf.parser.table_detector import detect_tables
from icpdf.parser.text_blocks import extract_text_blocks

ROOT = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((ROOT / "gold" / "generalization" / "spec.yaml")
                      .read_text(encoding="utf-8"))
GOLD = {record["item_id"]: record for record in (
    json.loads(line) for line in
    (ROOT / "gold" / "generalization" / "gold_table_set.jsonl")
    .read_text(encoding="utf-8").splitlines() if line)}


def _pdf(key: str) -> Path:
    path = Path(SPEC["pdfs"][key]["path"])
    if not path.is_file():
        pytest.skip(f"generalization PDF not available: {path}")
    return path


def _detected(pdf: Path, page_number: int):
    loaded = load_pdf(pdf)
    with fitz.open(str(pdf)) as doc:
        page = doc[page_number - 1]
        geometry = loaded.geometries[page_number - 1]
        blocks = extract_text_blocks(page, page_number, geometry)
        return detect_tables(blocks, page_number, TableParams(),
                             page=page, geometry=geometry)


def _iou(bbox, other) -> float:
    width = min(bbox[2], other[2]) - max(bbox[0], other[0])
    height = min(bbox[3], other[3]) - max(bbox[1], other[1])
    if width <= 0 or height <= 0:
        return 0.0
    inter = width * height
    union = (_pred_area(bbox) + _pred_area(other) - inter)
    return inter / union if union else 0.0


def _pred_area(bbox) -> float:
    return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])


def _matched(detected, item_id: str):
    item = GOLD[item_id]
    bbox = item["table"]["bbox"]
    table = max(detected, key=lambda candidate: _iou(candidate.bbox, bbox))
    assert _iou(table.bbox, bbox) >= 0.9, (item_id, [t.bbox for t in detected])
    assert table.page_number == item["page"]
    return table


def _roles(table):
    return {boundary.role: boundary for boundary in table.visual_boundary_evidence}


def test_micrf103_p03_visual_lattice_is_independent_of_the_physical_grid():
    detected = _detected(_pdf("micrf103"), 3)
    table = _matched(detected, "MICRF103-P03-T01")
    assert len(table.rows) == 30
    assert len({cell.column_index for row in table.rows for cell in row.cells}) == 6
    assert table.visual_boundary_status == "implied_outer"
    assert table.visual_columns == 6
    assert table.partial_boundaries == ()
    assert len(table.visual_boundaries) == 7
    roles = _roles(table)
    assert roles["outer_left"].drawn is False
    assert roles["outer_right"].drawn is False


def test_ds10cp152_partial_visual_separators():
    detected = _detected(_pdf("ds10cp152"), 4)
    table = _matched(detected, "DS10CP152-P04-T01")
    assert table.visual_boundary_status == "partial"
    assert table.visual_columns == 8
    assert table.partial_boundaries == pytest.approx((346.1,), abs=0.2)

    detected = _detected(_pdf("ds10cp152"), 5)
    table = _matched(detected, "DS10CP152-P05-T01")
    assert table.visual_boundary_status == "partial"
    assert table.visual_columns == 8
    assert table.partial_boundaries == pytest.approx((363.1,), abs=0.2)


@pytest.mark.parametrize("item_id,status,columns,partials", [
    ("CY29FCT520-P04-T01", "printed", 4, ()),
    ("CY29FCT520-P04-T02", "partial", 6, (173.2,)),
    ("CY29FCT520-P05-T01", "partial", 7, (193.9, 266.0)),
    ("CY29FCT520-P06-T01", "partial", 5, (290.2,)),
])
def test_cy29_visual_lattice(item_id, status, columns, partials):
    page = GOLD[item_id]["page"]
    table = _matched(_detected(_pdf("cy29fct520"), page), item_id)
    assert table.visual_boundary_status == status
    assert table.visual_columns == columns
    assert table.partial_boundaries == pytest.approx(partials, abs=0.5)


def test_not_printed_tables_keep_visual_columns_null():
    table = _matched(_detected(_pdf("ds10cp152"), 11), "DS10CP152-P11-T01")
    assert table.visual_boundary_status == "not_printed"
    assert table.visual_columns is None
    assert len(table.visual_boundaries) == 2
    assert table.partial_boundaries == ()
    assert {boundary.role for boundary in table.visual_boundary_evidence} == {
        "outer_left", "outer_right"}

    table = _matched(_detected(_pdf("cy29fct520"), 8), "CY29FCT520-P08-T01")
    assert table.visual_boundary_status == "not_printed"
    assert table.visual_columns is None
    assert len(table.visual_boundaries) == 2


def test_ds10cp152_p13_headerless_quad_table_visual():
    table = _matched(_detected(_pdf("ds10cp152"), 13), "DS10CP152-P13-T02")
    assert table.header_rows == 0
    assert len(table.rows) == 5
    assert table.visual_boundary_status == "printed"
    assert table.visual_columns == 2
    assert len(table.visual_boundaries) == 3


def test_cy29_package_outline_and_dimension_table_are_separate():
    detected = _detected(_pdf("cy29fct520"), 10)
    negative = next(item for item in SPEC["negatives"]
                    if item["id"] == "CY29FCT520-N03-P10")
    outline = next(table for table in detected
                   if _iou(table.bbox, tuple(negative["bbox"])) >= 0.9)
    assert outline.visual_boundary_status == "not_printed"
    assert outline.visual_columns is None

    dimension = _matched(detected, "CY29FCT520-P10-T01")
    assert dimension.visual_boundary_status == "printed"
    assert dimension.visual_columns == 3


def _coverage(boundary, table) -> float:
    y0, y1 = table.bbox[1], table.bbox[3]
    spans = sorted((max(y0, segment.y0), min(y1, segment.y1))
                   for segment in boundary.segments)
    total, start, end = 0.0, None, None
    for a, b in spans:
        if start is None:
            start, end = a, b
        elif a <= end + 2.5:
            end = max(end, b)
        else:
            total += end - start
            start, end = a, b
    if start is not None:
        total += end - start
    return total / (y1 - y0)


def test_visual_evidence_traces_to_components_and_primitives():
    table = _matched(_detected(_pdf("ds10cp152"), 4), "DS10CP152-P04-T01")
    for boundary in table.visual_boundary_evidence:
        assert boundary.segment_count == len(boundary.segments)
        assert boundary.component_ids == sorted(
            {segment.component_id for segment in boundary.segments})
        assert boundary.coverage == pytest.approx(_coverage(boundary, table),
                                                  abs=1e-6)
        if boundary.drawn:
            assert boundary.segments
            if boundary.role != "internal":
                assert boundary.coverage >= 0.85
            for segment in boundary.segments:
                assert segment.y1 > segment.y0
                assert segment.primitive_indices
                assert segment.primitive_indices == sorted(
                    set(segment.primitive_indices))
        elif boundary.coverage == 0.0:
            assert boundary.segments == []


def test_implied_outer_never_carries_drawn_line_evidence():
    table = _matched(_detected(_pdf("micrf103"), 3), "MICRF103-P03-T01")
    roles = _roles(table)
    for role in ("outer_left", "outer_right"):
        boundary = roles[role]
        assert boundary.drawn is False
        assert boundary.coverage == 0.0
        assert boundary.segments == []
        assert boundary.component_ids == []
