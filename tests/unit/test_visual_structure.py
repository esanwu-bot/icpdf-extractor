# -*- coding: utf-8 -*-
"""Synthetic tests for the S2a visual boundary lattice."""

from __future__ import annotations

import pytest

from icpdf.parser.config import (
    TABLE_PARAMS_SNAPSHOT_VERSION,
    TableParams,
    table_params_sha256,
    table_params_snapshot,
)
from icpdf.parser.layout import RuleComponent, RulePrimitive, RuleSegment
from icpdf.parser.structure import TableRegion
from icpdf.parser.visual_structure import build_visual_structure

BBOX = (0.0, 0.0, 300.0, 100.0)


def _v(x: float, y0: float = 0.0, y1: float = 100.0) -> RuleSegment:
    return RuleSegment("v", y0, y1, x)


def _region(verticals, bbox=BBOX, components=None) -> TableRegion:
    component = RuleComponent(bbox=bbox, horizontal=(), vertical=tuple(verticals),
                              page_number=1, component_id=0)
    members = tuple(components) if components is not None else (component,)
    return TableRegion(page_number=1, bbox=bbox, source="rule_lattice",
                       component=component, components=members,
                       boundary_source="ruled")


def _roles(structure):
    return {boundary.role: boundary for boundary in structure.boundaries}


def test_full_height_verticals_are_printed():
    structure = build_visual_structure(
        _region([_v(0.0), _v(100.0), _v(200.0), _v(300.0)]))
    assert structure.visual_boundary_status == "printed"
    assert structure.visual_columns == 3
    assert structure.visual_boundaries == (0.0, 100.0, 200.0, 300.0)
    assert structure.partial_boundaries == ()
    assert all(boundary.drawn for boundary in structure.boundaries)


def test_missing_outer_edges_are_implied():
    structure = build_visual_structure(_region([_v(100.0), _v(200.0)]))
    assert structure.visual_boundary_status == "implied_outer"
    assert structure.visual_columns == 3
    roles = _roles(structure)
    assert roles["outer_left"].drawn is False
    assert roles["outer_right"].drawn is False
    assert roles["outer_left"].coverage == 0.0


def test_single_implied_outer_still_implied_outer():
    """Reviewer rule: one implied side is enough; each side keeps its evidence."""
    structure = build_visual_structure(_region([_v(0.0), _v(100.0), _v(200.0)]))
    assert structure.visual_boundary_status == "implied_outer"
    roles = _roles(structure)
    assert roles["outer_left"].drawn is True
    assert roles["outer_right"].drawn is False


def test_partial_internal_boundary():
    structure = build_visual_structure(
        _region([_v(0.0), _v(100.0, 0.0, 40.0), _v(300.0)]))
    assert structure.visual_boundary_status == "partial"
    assert structure.visual_columns == 2
    assert structure.partial_boundaries == (100.0,)
    assert _roles(structure)["internal"].coverage == pytest.approx(0.4)


def test_partial_takes_precedence_over_implied_outer():
    structure = build_visual_structure(
        _region([_v(100.0, 0.0, 40.0), _v(200.0)]))
    assert structure.visual_boundary_status == "partial"


def test_not_printed_when_only_outer_edges_exist():
    structure = build_visual_structure(_region([_v(0.0), _v(300.0)]))
    assert structure.visual_boundary_status == "not_printed"
    assert structure.visual_columns is None
    assert structure.visual_boundaries == (0.0, 300.0)
    assert structure.partial_boundaries == ()
    assert [boundary.role for boundary in structure.boundaries] == [
        "outer_left", "outer_right"]


def test_text_alignment_region_has_no_visual_lattice():
    region = TableRegion(page_number=1, bbox=BBOX, source="text_alignment",
                         boundary_source="implied_alignment")
    structure = build_visual_structure(region)
    assert structure.visual_boundary_status == "not_printed"
    assert structure.visual_columns is None
    assert structure.visual_boundaries == (0.0, 300.0)


def test_short_segments_are_not_separators():
    structure = build_visual_structure(
        _region([_v(0.0), _v(100.0, 0.0, 3.9), _v(300.0)]),
        TableParams(visual_min_rule_span_pt=4.0))
    assert structure.visual_boundary_status == "not_printed"


def test_collinear_segments_are_merged_and_clipped():
    structure = build_visual_structure(
        _region([_v(0.0, -20.0, 130.0), _v(100.0, 0.0, 50.0),
                 _v(100.4, 50.0, 100.0), _v(300.0)]))
    assert structure.visual_boundary_status == "printed"
    internal = _roles(structure)["internal"]
    assert internal.coverage == pytest.approx(1.0)
    assert internal.segment_count == 2


def test_segment_gap_below_full_height():
    structure = build_visual_structure(
        _region([_v(0.0), _v(100.0, 0.0, 40.0), _v(100.2, 60.0, 100.0),
                 _v(300.0)]))
    assert structure.visual_boundary_status == "partial"
    assert structure.partial_boundaries == pytest.approx((100.1,))


def test_outer_edge_within_tolerance_is_drawn():
    structure = build_visual_structure(
        _region([_v(2.0), _v(100.0), _v(298.0)]))
    assert structure.visual_boundary_status == "printed"
    roles = _roles(structure)
    assert roles["outer_left"].drawn is True
    assert roles["outer_right"].drawn is True


def test_segments_are_collected_from_all_components():
    first = RuleComponent(bbox=(0.0, 0.0, 300.0, 50.0), horizontal=(),
                          vertical=(_v(0.0, 0.0, 50.0), _v(300.0, 0.0, 50.0)),
                          page_number=1, component_id=0)
    second = RuleComponent(bbox=(0.0, 50.0, 300.0, 100.0), horizontal=(),
                           vertical=(_v(0.0, 50.0, 100.0), _v(300.0, 50.0, 100.0),
                                     _v(150.0, 50.0, 100.0)),
                           page_number=1, component_id=1)
    region = TableRegion(page_number=1, bbox=BBOX, source="rule_lattice",
                         component=first, components=(first, second),
                         boundary_source="ruled")
    structure = build_visual_structure(region)
    assert structure.visual_columns == 2
    assert structure.visual_boundary_status == "partial"
    assert _roles(structure)["internal"].component_ids == [1]


def test_table_params_snapshot_contains_visual_defaults_and_hash():
    params = TableParams()
    snapshot = table_params_snapshot(params)
    assert snapshot["snapshot_version"] == TABLE_PARAMS_SNAPSHOT_VERSION
    assert snapshot["params"]["visual_min_rule_span_pt"] == 4.0
    assert snapshot["params"]["visual_boundary_tol_pt"] == 2.5
    assert snapshot["params"]["visual_full_height_coverage"] == 0.85
    assert table_params_sha256(params) == table_params_sha256(TableParams())
    changed = table_params_sha256(TableParams(visual_full_height_coverage=0.9))
    assert changed != table_params_sha256(params)


def test_left_implied_right_drawn_is_implied_outer():
    structure = build_visual_structure(
        _region([_v(100.0), _v(200.0), _v(300.0)]))
    assert structure.visual_boundary_status == "implied_outer"
    assert structure.partial_boundaries == ()
    roles = _roles(structure)
    assert roles["outer_left"].drawn is False
    assert roles["outer_right"].drawn is True


def test_both_outers_implied_with_full_internals():
    structure = build_visual_structure(
        _region([_v(100.0), _v(200.0)]))
    assert structure.visual_boundary_status == "implied_outer"
    assert structure.visual_columns == 3
    assert structure.partial_boundaries == ()
    assert all(boundary.coverage == 0.0 for boundary in
               (structure.boundaries[0], structure.boundaries[-1]))


def test_outer_coverage_deficit_alone_does_not_make_partial():
    """P1: a short outer rule is implied, never a partial internal boundary."""
    structure = build_visual_structure(
        _region([_v(0.0, 0.0, 50.0), _v(100.0), _v(200.0), _v(300.0)]))
    assert structure.visual_boundary_status == "implied_outer"
    assert structure.partial_boundaries == ()
    roles = _roles(structure)
    assert roles["outer_left"].drawn is False
    assert roles["outer_left"].coverage == pytest.approx(0.5)
    assert roles["outer_right"].drawn is True


def test_partial_internal_with_one_implied_outer_stays_partial():
    structure = build_visual_structure(
        _region([_v(100.0, 0.0, 40.0), _v(200.0), _v(300.0)]))
    assert structure.visual_boundary_status == "partial"
    assert structure.partial_boundaries == (100.0,)
    assert _roles(structure)["outer_left"].drawn is False


def test_grouping_is_order_independent():
    verticals = [_v(0.0), _v(100.0), _v(100.3), _v(200.0), _v(300.0)]
    forward = build_visual_structure(_region(verticals))
    reverse = build_visual_structure(_region(list(reversed(verticals))))
    assert forward.visual_boundaries == reverse.visual_boundaries
    assert forward.visual_boundary_status == reverse.visual_boundary_status
    assert [b.coverage for b in forward.boundaries] == \
        [b.coverage for b in reverse.boundaries]
    assert [b.segment_count for b in forward.boundaries] == \
        [b.segment_count for b in reverse.boundaries]


def test_anchor_grouping_prevents_chain_merge():
    """Segments drifting 2.4pt apart must not chain into one wide cluster."""
    structure = build_visual_structure(
        _region([_v(0.0), _v(100.0), _v(102.4), _v(104.4), _v(106.4),
                 _v(300.0)]))
    internal = [boundary for boundary in structure.boundaries
                if boundary.role == "internal"]
    assert [round(boundary.x, 1) for boundary in internal] == [101.2, 105.4]
    assert structure.visual_columns == 3


def test_segment_evidence_links_components_and_primitives():
    first = RulePrimitive(1, "line", "v", 0.0, 50.0, 100.0, 0.5, 3, 0, 0)
    second = RulePrimitive(1, "line", "v", 50.0, 100.0, 100.1, 0.5, 3, 1, 0)
    component = RuleComponent(
        bbox=BBOX, horizontal=(),
        vertical=(_v(0.0), _v(100.0, 0.0, 50.0), _v(100.1, 50.0, 100.0),
                  _v(300.0)),
        primitives=(first, second), primitive_indices=(4, 7),
        page_number=1, component_id=2)
    region = TableRegion(page_number=1, bbox=BBOX, source="rule_lattice",
                         component=component, components=(component,),
                         boundary_source="ruled")
    structure = build_visual_structure(region)
    boundary = _roles(structure)["internal"]
    assert boundary.component_ids == [2]
    assert boundary.segment_count == 2
    assert [(segment.component_id, segment.y0, segment.y1,
             segment.primitive_indices) for segment in boundary.segments] == [
        (2, 0.0, 50.0, [4]), (2, 50.0, 100.0, [7])]


def test_implied_outer_has_no_fabricated_segment():
    structure = build_visual_structure(
        _region([_v(100.0), _v(200.0), _v(300.0)]))
    left = _roles(structure)["outer_left"]
    assert left.drawn is False and left.coverage == 0.0
    assert left.segments == [] and left.component_ids == []
    assert left.segment_count == 0
