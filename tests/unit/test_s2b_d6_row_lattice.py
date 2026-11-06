# -*- coding: utf-8 -*-
"""D6: the physical row lattice survives detection and domain rebuild."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from icpdf.domain.table import (
    ReconstructionStatus,
    Table,
    TableRow,
    TableType,
)
from icpdf.parser.table_detector import (
    DetectedCell,
    DetectedRow,
    DetectedTable,
)
from icpdf.parser.table_rebuilder import build_table


def _detected() -> DetectedTable:
    cell = DetectedCell(
        text="3.3",
        bbox=(0.0, 0.0, 10.0, 10.0),
        column_index=0,
        word_ids=("p1-b0-l0-w0",),
    )
    row = DetectedRow(bbox=(0.0, 0.0, 10.0, 10.0), cells=[cell], grid_row=0)
    return DetectedTable(
        page_number=1,
        bbox=(0.0, 0.0, 10.0, 10.0),
        rows=[row],
        detection_method="rule_lattice",
        confidence=0.9,
        reconstruction_status=ReconstructionStatus.RECONSTRUCTED,
        grid_ys=(0.0, 10.0),
        n_rows=1,
    )


def _table(**kw) -> Table:
    detected = _detected()
    base = dict(
        table_id="p001-t01",
        document_id="doc-1",
        page_number=1,
        bbox=(0.0, 0.0, 10.0, 10.0),
        table_type=TableType.UNKNOWN,
        rows=[],
        detection_method="rule_lattice",
        confidence=0.9,
        reconstruction_status=ReconstructionStatus.RECONSTRUCTED,
        grid_ys=(0.0, 10.0),
        n_rows=1,
    )
    base.update(kw)
    return Table(**base)


def test_detected_table_persists_the_row_lattice():
    detected = _detected()
    assert detected.grid_ys == (0.0, 10.0)
    assert detected.n_rows == 1


def test_build_table_copies_the_row_lattice_and_word_ids():
    table = build_table(_detected(), "doc-1", 1)
    assert table.grid_ys == (0.0, 10.0)
    assert table.n_rows == 1
    assert table.rows[0].cells[0].word_ids == ("p1-b0-l0-w0",)


def test_domain_table_rejects_non_strict_row_lattice():
    with pytest.raises(ValidationError):
        _table(grid_ys=(0.0, 0.0, 10.0), n_rows=2)


def test_domain_table_rejects_row_count_mismatch():
    with pytest.raises(ValidationError):
        _table(grid_ys=(0.0, 10.0), n_rows=2)


def test_domain_table_keeps_legacy_defaults_loadable():
    table = _table(grid_ys=(), n_rows=0)
    assert table.grid_ys == ()
    assert table.n_rows == 0


def test_domain_table_rejects_single_coordinate_lattice():
    with pytest.raises(ValidationError):
        _table(grid_ys=(0.0,), n_rows=0)


def test_domain_table_rejects_non_finite_lattice():
    for bad in (float("nan"), float("inf")):
        with pytest.raises(ValidationError):
            _table(grid_ys=(0.0, bad), n_rows=1)


def _bare_detected(**kw) -> DetectedTable:
    base = dict(
        page_number=1,
        bbox=(0.0, 0.0, 10.0, 10.0),
        rows=[],
        detection_method="rule_lattice",
        confidence=0.9,
        reconstruction_status=ReconstructionStatus.RECONSTRUCTED,
    )
    base.update(kw)
    return DetectedTable(**base)


def test_detected_table_applies_the_same_lattice_rule():
    with pytest.raises(ValidationError):
        _bare_detected(grid_ys=(0.0,), n_rows=0)
    with pytest.raises(ValidationError):
        _bare_detected(grid_ys=(0.0, float("nan")), n_rows=1)
    with pytest.raises(ValidationError):
        _bare_detected(grid_ys=(0.0, 10.0), n_rows=2)


def test_detected_table_keeps_legacy_defaults_loadable():
    table = _bare_detected()
    assert table.grid_ys == ()
    assert table.n_rows == 0
