# -*- coding: utf-8 -*-
"""Phase 1.1 coordinate-chain audit: rotations, CropBox, pixel mapping."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pymupdf as fitz
import pytest
from PIL import Image

from icpdf.parser.config import load_config
from icpdf.parser.coords import PageGeometry
from icpdf.parser.page_renderer import render_page
from icpdf.parser.pdf_loader import load_pdf
from icpdf.parser.pipeline import parse_pdf
from icpdf.parser.text_blocks import extract_text_blocks
from tests.fixtures import synthetic


def _word_bbox(pdf: Path, page_number: int = 1):
    loaded = load_pdf(pdf)
    with fitz.open(str(pdf)) as doc:
        block = extract_text_blocks(doc[page_number - 1], page_number,
                                    loaded.geometries[page_number - 1])
    return loaded.geometries[page_number - 1], block[0].lines[0].words[0].bbox


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_rotation_bbox_lands_in_display_space(tmp_path: Path, rotation: int):
    pdf = synthetic.marker_pdf(tmp_path / f"r{rotation}.pdf", rotation=rotation)
    geometry, bbox = _word_bbox(pdf)
    assert geometry.rotation == rotation
    # Raw get_text bbox is (100, 87.1, 151.34, 103.59) in unrotated space.
    expected = {
        0: (100.0, 87.1, 151.34, 103.59),
        90: (792.0 - 103.59, 100.0, 792.0 - 87.1, 151.34),
        180: (612.0 - 151.34, 792.0 - 103.59, 612.0 - 100.0, 792.0 - 87.1),
        270: (87.1, 612.0 - 151.34, 103.59, 612.0 - 100.0),
    }[rotation]
    assert bbox == pytest.approx(expected, abs=1.0)
    rect = geometry.rect
    assert rect[0] <= bbox[0] and bbox[2] <= rect[2]
    assert rect[1] <= bbox[1] and bbox[3] <= rect[3]


def test_cropbox_offset_is_subtracted(tmp_path: Path):
    pdf = synthetic.marker_pdf(tmp_path / "crop.pdf", crop=(50, 50, 562, 742))
    geometry, bbox = _word_bbox(pdf)
    assert geometry.rect == (0.0, 0.0, 512.0, 692.0)
    assert bbox == pytest.approx((50.0, 37.1, 101.34, 53.59), abs=1.0)


def test_cropbox_plus_rotation(tmp_path: Path):
    pdf = synthetic.marker_pdf(tmp_path / "crop_rot.pdf", rotation=90,
                               crop=(50, 50, 562, 742))
    geometry, bbox = _word_bbox(pdf)
    assert geometry.rect == (0.0, 0.0, 692.0, 512.0)
    assert bbox == pytest.approx((692.0 - 53.59, 50.0, 692.0 - 37.1, 101.34), abs=1.0)


@pytest.mark.parametrize("rotation", [0, 90])
def test_render_pixel_matches_word_bbox(tmp_path: Path, rotation: int):
    pdf = synthetic.marker_pdf(tmp_path / f"pix{rotation}.pdf", rotation=rotation)
    out = tmp_path / f"page{rotation}.png"
    geometry = render_page(pdf, 1, out, dpi=150)
    _, bbox = _word_bbox(pdf)
    px = geometry.bbox_to_pixel(bbox)
    back = geometry.pixel_to_bbox(px)
    assert back == pytest.approx(bbox, abs=0.5)
    image = Image.open(out).convert("L")
    assert image.size == (geometry.pixel_width, geometry.pixel_height)
    crop = image.crop(tuple(round(v) for v in px))
    assert crop.getextrema()[0] < 200, "rendered crop contains no ink at the mapped bbox"


def test_effective_config_and_hash_are_recorded(tmp_path: Path):
    cfg_path = tmp_path / "parser.yaml"
    cfg_path.write_text(
        "pdf:\n  render_dpi: 96\n  text_min_chars: 1\n"
        "tables:\n  cell_gap_pt: 20.0\n  row_gap_factor: 2.5\n"
        "  column_tolerance: 2\n  header_min_hits: 2\n  max_title_chars: 120\n",
        encoding="utf-8")
    pdf = synthetic.simple_three_column(tmp_path / "simple.pdf")
    result = parse_pdf(pdf, "CFG1", tmp_path / "runs", config_path=cfg_path)
    manifest = json.loads((Path(result["run_dir"]) / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["parser_config"]["tables"]["cell_gap_pt"] == 20.0
    assert manifest["parser_config"]["pdf"]["render_dpi"] == 96
    expected = hashlib.sha256(cfg_path.read_bytes()).hexdigest()
    assert manifest["parser_config_sha256"] == expected
    assert load_config(cfg_path)[1] == expected
