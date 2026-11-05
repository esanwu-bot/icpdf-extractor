# -*- coding: utf-8 -*-
"""Phase 1 integration tests against synthetic PDFs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from icpdf.parser.candidate_registry import build_candidates
from icpdf.parser.coords import PageGeometry
from icpdf.parser.page_renderer import render_page
from icpdf.parser.pdf_loader import PDFEncryptedError, PDFLoadError, load_pdf
from icpdf.parser.pipeline import parse_pdf
from tests.fixtures import synthetic


def test_loader_identity_and_geometry(tmp_path: Path):
    pdf = synthetic.simple_three_column(tmp_path / "simple.pdf")
    loaded = load_pdf(pdf)
    assert loaded.document.sha256 == loaded.sha256
    assert loaded.document.page_count == 1
    assert loaded.geometries[0].pixel_width > 0


def test_bbox_pixel_roundtrip_on_rotated_page(tmp_path: Path):
    pdf = synthetic.rotated_page(tmp_path / "rotated.pdf")
    geometry = load_pdf(pdf, dpi=150).geometries[0]
    bbox = (10.0, 20.0, 110.0, 60.0)
    pixel = geometry.bbox_to_pixel(bbox)
    back = geometry.pixel_to_bbox(pixel)
    assert all(abs(a - b) <= 0.5 for a, b in zip(bbox, back))


def test_render_page_creates_png(tmp_path: Path):
    pdf = synthetic.simple_three_column(tmp_path / "simple.pdf")
    out = tmp_path / "page.png"
    geometry = render_page(pdf, 1, out)
    assert out.is_file() and out.stat().st_size > 0
    assert isinstance(geometry, PageGeometry)


def test_no_text_layer_yields_no_candidates(tmp_path: Path):
    pdf = synthetic.no_text_layer(tmp_path / "blank.pdf")
    result = parse_pdf(pdf, "BLANK1", tmp_path / "runs")
    assert result["tables"] == 0 and result["candidates"] == 0


def test_corrupt_pdf_is_rejected(tmp_path: Path):
    pdf = synthetic.corrupt_pdf(tmp_path / "bad.pdf")
    with pytest.raises(PDFLoadError):
        load_pdf(pdf)


def test_duplicate_value_in_two_tables_stays_separate(tmp_path: Path):
    pdf = synthetic.duplicate_value_two_tables(tmp_path / "dupe.pdf")
    result = parse_pdf(pdf, "DUPE1", tmp_path / "runs")
    run_dir = Path(result["run_dir"])
    data = json.loads((run_dir / "candidates.json").read_text(encoding="utf-8"))
    three = [c for c in data["candidates"] if c["raw_text"].strip() == "3.3"]
    assert len(three) >= 2
    table_ids = {c["table_id"] for c in three}
    assert len(table_ids) >= 2
    tables = json.loads((run_dir / "tables.json").read_text(encoding="utf-8"))
    types = {t["table_type"] for t in tables}
    assert "recommended_operating" in types and "absolute_maximum" in types


def test_incomplete_table_is_partial_not_reconstructed(tmp_path: Path):
    pdf = synthetic.incomplete_table(tmp_path / "ragged.pdf")
    result = parse_pdf(pdf, "RAGGED1", tmp_path / "runs")
    tables = json.loads((Path(result["run_dir"]) / "tables.json").read_text(encoding="utf-8"))
    assert tables
    assert tables[0]["reconstruction_status"] in ("partial", "unresolved")


def test_multipage_tables_keep_page_binding(tmp_path: Path):
    pdf = synthetic.multipage_table(tmp_path / "multi.pdf")
    result = parse_pdf(pdf, "MULTI1", tmp_path / "runs")
    assert result["page_count"] == 2
    tables = json.loads((Path(result["run_dir"]) / "tables.json").read_text(encoding="utf-8"))
    assert {t["page_number"] for t in tables} == {1, 2}


def test_candidate_ids_unique_and_table_bound(tmp_path: Path):
    pdf = synthetic.duplicate_value_two_tables(tmp_path / "dupe.pdf")
    loaded = load_pdf(pdf)
    result = parse_pdf(pdf, "DUPE2", tmp_path / "runs")
    data = json.loads((Path(result["run_dir"]) / "candidates.json").read_text(encoding="utf-8"))
    ids = [c["candidate_id"] for c in data["candidates"]]
    assert len(ids) == len(set(ids))
    assert all(c["document_id"] == loaded.document.document_id for c in data["candidates"])
    assert all(c["table_id"] and c["row_id"] and c["cell_id"] for c in data["candidates"])


def test_rotated_text_keeps_bbox_inside_page(tmp_path: Path):
    pdf = synthetic.rotated_text(tmp_path / "rotated_text.pdf")
    loaded = load_pdf(pdf)
    result = parse_pdf(pdf, "ROT1", tmp_path / "runs")
    blocks = json.loads((Path(result["run_dir"]) / "text_blocks.json").read_text(encoding="utf-8"))
    assert blocks
    rect = loaded.geometries[0].rect
    for block in blocks:
        x0, y0, x1, y1 = block["bbox"]
        assert rect[0] <= x0 <= x1 <= rect[2]
        assert rect[1] <= y0 <= y1 <= rect[3]


def test_multi_mpn_document_parses_without_merging_identity(tmp_path: Path):
    pdf = synthetic.multi_mpn(tmp_path / "multi_mpn.pdf")
    result = parse_pdf(pdf, "MPN-A", tmp_path / "runs")
    product = json.loads((Path(result["run_dir"]) / "product.json").read_text(encoding="utf-8"))
    assert product["requested_mpn"] == "MPN-A"
    assert product["normalized_mpn"] == "MPN-A"


def test_run_artifacts_and_secret_redaction(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-should-not-appear")
    pdf = synthetic.simple_three_column(tmp_path / "simple.pdf")
    result = parse_pdf(pdf, "SIMPLE1", tmp_path / "runs")
    run_dir = Path(result["run_dir"])
    for name in ("document.json", "text_blocks.json", "tables.json",
                 "candidates.json", "run_config.json", "run_manifest.json"):
        assert (run_dir / name).is_file()
    config = (run_dir / "run_config.json").read_text(encoding="utf-8")
    assert "sk-should-not-appear" not in config
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["document_sha256"] == result["document_sha256"]
