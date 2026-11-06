# -*- coding: utf-8 -*-
"""Independent audit: visual boundary evidence vs raw PDF primitives.

Unlike the evidence validator, this test re-opens the PDF, re-runs
``collect_primitives`` and resolves every recorded ``primitive_indices`` entry
to the real ``RulePrimitive``.  It proves the recorded provenance is not merely
self-consistent: the primitive must exist on the page, be vertical, sit at the
boundary x, fall inside the segment's y-span, belong to the recorded
``RuleComponent``, and reproduce the stored coverage.

The PDFs live outside the repository; these tests skip when they are absent.
"""

from __future__ import annotations

import json
import shutil
from functools import lru_cache
from pathlib import Path

import pymupdf as fitz
import pytest
import yaml

from icpdf.parser.config import TableParams
from icpdf.parser.pdf_loader import load_pdf
from icpdf.parser.rule_primitives import (
    GRID_TOL,
    build_components,
    collect_primitives,
)
from icpdf.parser.table_detector import detect_tables
from icpdf.parser.text_blocks import extract_text_blocks
import tools.audit_visual_primitives as audit_tool
from tools.audit_visual_primitives import (
    AuditIdentityError,
    audit_table,
    primitive_index_space,
    raw_coverage,
    verify_identity,
)

ROOT = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((ROOT / "gold" / "generalization" / "spec.yaml")
                      .read_text(encoding="utf-8"))
GOLD = {record["item_id"]: record for record in (
    json.loads(line) for line in
    (ROOT / "gold" / "generalization" / "gold_table_set.jsonl")
    .read_text(encoding="utf-8").splitlines() if line)}

PARAMS = TableParams()


def _pdf(key: str) -> Path:
    path = Path(SPEC["pdfs"][key]["path"])
    if not path.is_file():
        pytest.skip(f"generalization PDF not available: {path}")
    return path


def _run_for(key: str) -> Path:
    label = SPEC["pdfs"][key]["label"]
    root = ROOT / "runs" / "phase14_s2a" / "review_r1" / "final_generalization"
    for manifest in root.glob("*/run_manifest.json"):
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        if payload.get("requested_mpn") == label:
            return manifest.parent
    pytest.skip(f"frozen run not available for {label}")


def _iou(bbox, other) -> float:
    width = min(bbox[2], other[2]) - max(bbox[0], other[0])
    height = min(bbox[3], other[3]) - max(bbox[1], other[1])
    if width <= 0 or height <= 0:
        return 0.0
    inter = width * height
    area = lambda box: max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])
    union = area(bbox) + area(other) - inter
    return inter / union if union else 0.0


def _matched(tables, item_id: str):
    item = GOLD[item_id]
    bbox = item["table"]["bbox"]
    table = max(tables, key=lambda candidate: _iou(candidate.bbox, bbox))
    assert _iou(table.bbox, bbox) >= 0.9, (item_id, [t.bbox for t in tables])
    assert table.page_number == item["page"]
    return table


@lru_cache(maxsize=None)
def _prepare(key: str, page_number: int, item_id: str):
    """Detect the table and rebuild the raw primitive/component world."""
    pdf = _pdf(key)
    loaded = load_pdf(pdf)
    assert loaded.sha256 == SPEC["pdfs"][key]["sha256"]
    with fitz.open(str(pdf)) as document:
        page = document[page_number - 1]
        geometry = loaded.geometries[page_number - 1]
        blocks = extract_text_blocks(page, page_number, geometry)
        tables = detect_tables(blocks, page_number, PARAMS,
                               page=page, geometry=geometry)
        primitives = collect_primitives(page, page_number, geometry)
        components = build_components(
            primitives, page_number=page_number, tol=GRID_TOL,
            min_width=PARAMS.rule_min_width_pt,
            min_height=PARAMS.rule_min_height_pt)
    return (_matched(tables, item_id), tuple(primitives), tuple(components))


def _issues(table, primitives, components):
    return audit_table(table, primitives=list(primitives),
                       components=list(components), params=PARAMS)


def _boundary(table, role=None, near=None):
    for boundary in table.visual_boundary_evidence:
        if role is not None and boundary.role != role:
            continue
        if near is not None and abs(boundary.x - near) > 0.5:
            continue
        return boundary
    raise AssertionError(f"no {role} boundary near {near}")


def _max_raw_coverage_at(bbox, primitives, x: float, tol: float = 2.5) -> float:
    spans = [(max(bbox[1], primitive.a), min(bbox[3], primitive.b))
             for primitive in primitives
             if primitive.orientation == "v" and abs(primitive.c - x) <= tol]
    spans = [(start, end) for start, end in spans if end > start]
    height = bbox[3] - bbox[1]
    if not spans or height <= 0:
        return 0.0
    spans.sort()
    total = 0.0
    start, end = spans[0]
    for next_start, next_end in spans[1:]:
        if next_start <= end + tol:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    return (total + end - start) / height


def _tampered(table, boundary, segment):
    evidence = list(table.visual_boundary_evidence)
    evidence[evidence.index(boundary)] = boundary.model_copy(
        update={"segments": [segment]})
    return table.model_copy(update={"visual_boundary_evidence": tuple(evidence)})


def test_ds10_internal_partial_traces_to_raw_primitives():
    table, primitives, components = _prepare("ds10cp152", 4, "DS10CP152-P04-T01")
    assert table.visual_boundary_status == "partial"
    assert _issues(table, primitives, components) == []

    boundary = _boundary(table, "internal", near=346.1)
    assert boundary.drawn is True
    assert boundary.coverage == pytest.approx(0.1082, abs=5e-4)
    recomputed = raw_coverage(boundary, table.bbox, list(primitives),
                              tol=PARAMS.visual_boundary_tol_pt)
    assert recomputed == pytest.approx(boundary.coverage, abs=1e-9)

    component = next(item for item in components
                     if item.component_id == boundary.component_ids[0])
    resolved = [primitives[index] for segment in boundary.segments
                for index in segment.primitive_indices]
    assert resolved
    assert all(primitive.page_number == 4 for primitive in resolved)
    assert all(primitive.orientation == "v" for primitive in resolved)
    assert all(abs(primitive.c - boundary.x) <= PARAMS.visual_boundary_tol_pt
               for primitive in resolved)
    assert all(index in component.primitive_indices
               for segment in boundary.segments
               for index in segment.primitive_indices)
    assert sorted({primitive.drawing_index for primitive in resolved}) == [278, 295]


def test_micrf_implied_outer_has_no_primitive_backing():
    table, primitives, components = _prepare("micrf103", 3, "MICRF103-P03-T01")
    assert table.visual_boundary_status == "implied_outer"
    assert table.visual_columns == 6
    assert _issues(table, primitives, components) == []

    for side, x in (("outer_left", table.bbox[0]), ("outer_right", table.bbox[2])):
        boundary = _boundary(table, side)
        assert boundary.x == pytest.approx(x, abs=0.01)
        assert boundary.drawn is False
        assert boundary.coverage == 0.0
        assert boundary.segments == []
        assert boundary.component_ids == []
        assert _max_raw_coverage_at(table.bbox, primitives, x) < (
            PARAMS.visual_full_height_coverage)

    internal = _boundary(table, "internal")
    assert internal.drawn is True
    assert raw_coverage(internal, table.bbox, list(primitives),
                        tol=PARAMS.visual_boundary_tol_pt) == pytest.approx(
                            internal.coverage, abs=1e-9)


def test_cy29_multiple_partial_boundaries_recompute_from_primitives():
    table, primitives, components = _prepare("cy29fct520", 5, "CY29FCT520-P05-T01")
    assert table.visual_boundary_status == "partial"
    assert table.partial_boundaries == pytest.approx((193.9, 266.0), abs=0.5)
    assert _issues(table, primitives, components) == []

    for boundary in table.visual_boundary_evidence:
        if boundary.role == "internal":
            recomputed = raw_coverage(boundary, table.bbox, list(primitives),
                                      tol=PARAMS.visual_boundary_tol_pt)
            assert recomputed == pytest.approx(boundary.coverage, abs=1e-9)
            if boundary.x in table.partial_boundaries:
                assert recomputed < PARAMS.visual_full_height_coverage
            else:
                assert recomputed >= PARAMS.visual_full_height_coverage


def test_primitive_index_space_is_collect_primitives_order_not_drawing_index():
    table, primitives, components = _prepare("ds10cp152", 4, "DS10CP152-P04-T01")
    space = primitive_index_space(list(primitives))
    assert space["primitives"] == 442
    assert space["index_ne_drawing_index"] > 0
    # The two numbering spaces really diverge on this page.
    assert len(primitives) != max(p.drawing_index for p in primitives) + 1

    for boundary in table.visual_boundary_evidence:
        for segment in boundary.segments:
            for index in segment.primitive_indices:
                primitive = primitives[index]
                assert primitive.orientation == "v"
                assert (index == primitive.drawing_index
                        or space["index_ne_drawing_index"] > 0)
    # A real example: index 363 resolves to drawing 362 (two lines from one item).
    mismatched = [index for index, primitive in enumerate(primitives)
                  if index != primitive.drawing_index]
    assert mismatched
    assert primitives[mismatched[0]].drawing_index != mismatched[0]
    assert _issues(table, primitives, components) == []


def test_tampered_primitive_index_fails_the_audit():
    table, primitives, components = _prepare("ds10cp152", 4, "DS10CP152-P04-T01")
    boundary = _boundary(table, "internal", near=346.1)
    segment = boundary.segments[0]

    out_of_range = segment.model_copy(
        update={"primitive_indices": [len(primitives) + 7]})
    codes = {issue.code for issue in _issues(
        _tampered(table, boundary, out_of_range), primitives, components)}
    assert "PRIMITIVE_INDEX_OUT_OF_RANGE" in codes

    horizontal = next(index for index, primitive in enumerate(primitives)
                      if primitive.orientation == "h")
    wrong_orientation = segment.model_copy(
        update={"primitive_indices": [horizontal]})
    codes = {issue.code for issue in _issues(
        _tampered(table, boundary, wrong_orientation), primitives, components)}
    assert "PRIMITIVE_NOT_VERTICAL" in codes
    assert "PRIMITIVE_NOT_IN_COMPONENT" in codes


def test_tampered_segment_span_fails_the_audit():
    table, primitives, components = _prepare("ds10cp152", 4, "DS10CP152-P04-T01")
    boundary = _boundary(table, "internal", near=346.1)
    segment = boundary.segments[0]

    stretched = segment.model_copy(update={"y1": segment.y1 + 9.0})
    codes = {issue.code for issue in _issues(
        _tampered(table, boundary, stretched), primitives, components)}
    assert "SEGMENT_SPAN_MISMATCH" in codes

    shifted = segment.model_copy(update={"y0": segment.y0 - 9.0})
    codes = {issue.code for issue in _issues(
        _tampered(table, boundary, shifted), primitives, components)}
    assert "SEGMENT_SPAN_MISMATCH" in codes


def test_drawn_outer_without_segments_fails_the_audit():
    table, primitives, components = _prepare("micrf103", 3, "MICRF103-P03-T01")
    boundary = _boundary(table, "outer_left")
    faked = boundary.model_copy(update={"drawn": True})
    evidence = list(table.visual_boundary_evidence)
    evidence[evidence.index(boundary)] = faked
    codes = {issue.code for issue in _issues(
        table.model_copy(update={"visual_boundary_evidence": tuple(evidence)}),
        primitives, components)}
    assert "DRAWN_WITHOUT_SEGMENTS" in codes
    assert "DRAWN_BELOW_FULL" in codes


def test_run_identity_matches_spec_and_manifest():
    for key in ("micrf103", "ds10cp152", "cy29fct520"):
        identity = verify_identity(_run_for(key))
        assert identity["document_sha256"] == SPEC["pdfs"][key]["sha256"]
        assert identity["page_count"] > 0
        assert identity["table_params_sha256"]
        assert identity["parser_config_sha256"]

    grid_tol = identity["grid_tol"]
    assert grid_tol["value"] == GRID_TOL
    assert grid_tol["build_components_default"] == GRID_TOL
    assert grid_tol["rule_components_default"] == GRID_TOL
    assert grid_tol["s1_defaults_match"] is True
    assert grid_tol["in_table_params"] is False
    assert grid_tol["s1_frozen_commit"] == (
        "3fc45195d8da20d95dd30ef87ef19859d3d2e002")
    assert grid_tol["s1_frozen_sha256"] == grid_tol["source_sha256"]
    assert grid_tol["frozen_baseline_match"] is True


def test_s1_frozen_baseline_drift_is_refused(monkeypatch):
    monkeypatch.setattr(audit_tool, "S1_FROZEN_RULE_PRIMITIVES_SHA256",
                        "0" * 64)
    with pytest.raises(AuditIdentityError) as raised:
        verify_identity(_run_for("micrf103"))
    assert any("does not match the S1 frozen baseline" in error
               for error in raised.value.errors)


def test_manifest_missing_required_artifact_is_refused(tmp_path):
    source_run = _run_for("micrf103")
    staged = tmp_path / "run"
    (staged / "pages").mkdir(parents=True)
    manifest = json.loads((source_run / "run_manifest.json")
                          .read_text(encoding="utf-8"))
    manifest["artifacts"] = [artifact for artifact in manifest["artifacts"]
                             if artifact["name"] != "tables.json"]
    (staged / "run_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8", newline="\n")
    for name in ("run_config.json", "document.json", "tables.json"):
        shutil.copy2(source_run / name, staged / name)
    shutil.copy2(source_run / "pages" / "geometry.json",
                 staged / "pages" / "geometry.json")
    shutil.copy2(source_run / "source.pdf", staged / "source.pdf")

    with pytest.raises(AuditIdentityError) as raised:
        verify_identity(staged)
    assert any("does not record artifact tables.json" in error
               for error in raised.value.errors)


def test_wrong_version_pdf_is_refused(tmp_path):
    source_run = _run_for("micrf103")
    staged = tmp_path / "run"
    (staged / "pages").mkdir(parents=True)
    for name in ("run_manifest.json", "run_config.json", "document.json",
                 "tables.json"):
        shutil.copy2(source_run / name, staged / name)
    shutil.copy2(source_run / "pages" / "geometry.json",
                 staged / "pages" / "geometry.json")
    # Same filename family, different document: identity must fail closed.
    shutil.copy2(_pdf("ds10cp152"), staged / "source.pdf")

    with pytest.raises(AuditIdentityError) as raised:
        verify_identity(staged)
    assert any("source.pdf sha256" in error for error in raised.value.errors)


def test_duplicate_primitive_in_one_boundary_fails_the_audit():
    table, primitives, components = _prepare("ds10cp152", 4, "DS10CP152-P04-T01")
    boundary = _boundary(table, "internal", near=346.1)
    segment = boundary.segments[0]
    duplicated = segment.model_copy(
        update={"primitive_indices": list(segment.primitive_indices) * 2})
    codes = {issue.code for issue in _issues(
        _tampered(table, boundary, duplicated), primitives, components)}
    assert "PRIMITIVE_DUPLICATE_IN_BOUNDARY" in codes


def test_cross_component_primitive_reference_fails_the_audit():
    table, primitives, components = _prepare("micrf103", 3, "MICRF103-P03-T01")
    boundary = _boundary(table, "internal", near=184.08)
    segment = boundary.segments[0]
    other_id = next(component_id for component_id in boundary.component_ids
                    if component_id != segment.component_id)
    crossed = segment.model_copy(update={"component_id": other_id})
    codes = {issue.code for issue in _issues(
        _tampered(table, boundary, crossed), primitives, components)}
    assert "PRIMITIVE_NOT_IN_COMPONENT" in codes
