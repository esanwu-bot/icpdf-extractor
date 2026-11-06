# -*- coding: utf-8 -*-
"""S1 unit tests: ruling primitives, provenance and connected components."""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz

from icpdf.parser.rule_primitives import (
    build_components,
    collect_primitives,
    merge_primitives,
)
from tests.fixtures import synthetic


def test_line_and_thin_rect_keep_source_indices(tmp_path: Path):
    pdf = synthetic.simple_three_column(tmp_path / "lines.pdf")
    doc = fitz.open(str(pdf))
    page = doc[0]
    page.draw_line((50, 300), (450, 300), color=(0, 0, 0), width=0.8)
    page.draw_rect(fitz.Rect(50, 320, 300, 320.8), color=(0, 0, 0), width=0.5)
    primitives = collect_primitives(page, 1)
    doc.close()

    lines = [item for item in primitives if item.kind == "line"]
    rects = [item for item in primitives if item.kind == "thin_rect"]
    assert len(lines) == 1 and len(rects) == 1
    assert lines[0].orientation == "h"
    assert (lines[0].a, lines[0].b, lines[0].c) == (50.0, 450.0, 300.0)
    assert lines[0].drawing_index >= 0 and lines[0].item_index >= 0
    assert rects[0].orientation == "h"
    assert (rects[0].a, rects[0].b) == (50.0, 300.0)


def test_quad_outline_emits_four_edges(tmp_path: Path):
    pdf = synthetic.quad_ruled_grid(tmp_path / "quad.pdf", rows=2, columns=2,
                                    x0=80, y0=100, cell_width=100,
                                    cell_height=14)
    doc = fitz.open(str(pdf))
    primitives = collect_primitives(doc[0], 1)
    doc.close()

    quads = [item for item in primitives if item.kind == "quad_edge"]
    assert len(quads) == 4 * 4
    for cell in range(4):
        edges = quads[cell * 4:(cell + 1) * 4]
        assert [edge.edge_index for edge in edges] == [0, 1, 2, 3]
        assert [edge.orientation for edge in edges] == ["h", "h", "v", "v"]
        assert len({edge.drawing_index for edge in edges}) == 1
    assert {edge.page_number for edge in quads} == {1}


def test_diagonal_quad_contributes_no_primitive(tmp_path: Path):
    pdf = synthetic.quad_ruled_grid(tmp_path / "diag.pdf", rows=2, columns=2,
                                    x0=80, y0=100, cell_width=100,
                                    cell_height=14, diagonal=True)
    doc = fitz.open(str(pdf))
    primitives = collect_primitives(doc[0], 1)
    doc.close()
    assert len([item for item in primitives if item.kind == "quad_edge"]) == 12


def test_thick_quad_is_decoration(tmp_path: Path):
    doc = fitz.open()
    page = doc.new_page()
    quad = fitz.Quad(fitz.Point(50, 50), fitz.Point(250, 50),
                     fitz.Point(50, 90), fitz.Point(250, 90))
    page.draw_quad(quad, color=(0, 0, 0), width=8)
    primitives = collect_primitives(page, 1)
    doc.close()
    assert primitives == []


def test_merge_primitives_keeps_both_sources(tmp_path: Path):
    pdf = synthetic.simple_three_column(tmp_path / "collinear.pdf")
    doc = fitz.open(str(pdf))
    page = doc[0]
    page.draw_line((50, 400), (200, 400), color=(0, 0, 0), width=0.8)
    page.draw_line((201, 400), (450, 400), color=(0, 0, 0), width=0.8)
    primitives = collect_primitives(page, 1)
    merged = [(segment, indices) for segment, indices in
              merge_primitives(primitives) if segment.orientation == "h"
              and abs(segment.c - 400.0) < 0.5]
    doc.close()
    assert len(merged) == 1
    segment, indices = merged[0]
    assert (segment.a, segment.b) == (50.0, 450.0)
    assert len(indices) == 2


def test_quad_grid_forms_one_component(tmp_path: Path):
    pdf = synthetic.quad_ruled_grid(tmp_path / "quad.pdf", rows=5, columns=2,
                                    x0=80, y0=100, cell_width=120,
                                    cell_height=14)
    doc = fitz.open(str(pdf))
    primitives = collect_primitives(doc[0], 1)
    components = build_components(primitives, page_number=1)
    doc.close()

    assert len(components) == 1
    component = components[0]
    assert component.bbox == (80.0, 100.0, 320.0, 170.0)
    assert len(component.horizontal) == 6 and len(component.vertical) == 3
    assert component.primitive_indices
    assert len(component.primitives) == len(component.primitive_indices)
    assert all(item.kind == "quad_edge" for item in component.primitives)
