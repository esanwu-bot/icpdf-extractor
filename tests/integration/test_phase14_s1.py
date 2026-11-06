# -*- coding: utf-8 -*-
"""S1 integration tests against the frozen generalization PDFs.

The PDFs live outside the repository (vendor datasheets); the tests skip when
they are absent.  Paths come from the Gold v2 spec, never from a hard-coded
vendor rule in the parser.
"""

from __future__ import annotations

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


def _overlaps(bbox, other) -> float:
    width = min(bbox[2], other[2]) - max(bbox[0], other[0])
    height = min(bbox[3], other[3]) - max(bbox[1], other[1])
    if width <= 0 or height <= 0:
        return 0.0
    pred_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
    return (width * height) / pred_area if pred_area else 0.0


def test_micrf103_p03_merges_five_components_into_one_region():
    pdf = _pdf("micrf103")
    detected = [table for table in _detected(pdf, 3)
                if table.page_number == 3]
    gold_bbox = (46.8, 186.5, 586.8, 732.0)
    covering = [table for table in detected
                if _overlaps(table.bbox, gold_bbox) >= 0.9]
    assert len(covering) == 1, [table.bbox for table in detected]
    table = covering[0]
    assert table.bbox == pytest.approx(gold_bbox, abs=2.0)
    assert table.region_components == [0, 1, 2, 3, 4]
    assert table.boundary_source in ("implied_horizontal", "mixed")
    assert any(item.startswith("merge:") for item in table.merge_evidence)
    assert any(item.startswith("absorbed:") for item in table.merge_evidence)


def test_ds10cp152_p13_quad_ruled_label_table_is_detected():
    pdf = _pdf("ds10cp152")
    detected = [table for table in _detected(pdf, 13)
                if table.page_number == 13]
    gold_bbox = (257.4, 213.4, 505.8, 264.0)
    covering = [table for table in detected
                if _overlaps(table.bbox, gold_bbox) >= 0.9]
    assert len(covering) == 1, [table.bbox for table in detected]
    table = covering[0]
    assert table.bbox == pytest.approx(gold_bbox, abs=2.0)
    assert table.header_rows == 0
    assert len(table.rows) == 5
    assert sorted(cell.column_index for cell in table.rows[0].cells) == [0, 1]
    labels = [cell.text for row in table.rows for cell in row.cells
              if cell.column_index == 0]
    assert labels == ["A0", "B0", "K0", "W", "P1"]


def _negative_bbox(identifier: str):
    for item in SPEC["negatives"]:
        if item["id"] == identifier:
            return tuple(item["bbox"])
    raise KeyError(identifier)


@pytest.mark.parametrize("negative_id", [
    "CY29FCT520-N01-P01",
    "CY29FCT520-N02-P02",
    "CY29FCT520-N03-P10",
])
def test_cy29_graphics_are_not_claimed_as_solved(negative_id: str):
    """S1 keeps drawings as negatives; classification is S3 work.

    The pinout no longer produces a candidate.  The block diagram and package
    drawing still do, so this test is xfail until the S3 drawing gate exists.
    """
    pdf = _pdf("cy29fct520")
    page_number = {item["id"]: item["page"]
                   for item in SPEC["negatives"]}[negative_id]
    bbox = _negative_bbox(negative_id)
    detected = _detected(pdf, page_number)
    offending = [table for table in detected
                 if _overlaps(table.bbox, bbox) >= 0.25]
    if offending and negative_id != "CY29FCT520-N01-P01":
        pytest.xfail("S3 drawing/schematic gate not implemented in S1")
    assert offending == []
