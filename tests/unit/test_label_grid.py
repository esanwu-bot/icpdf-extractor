# -*- coding: utf-8 -*-
"""Negative and positive cases for the headerless label-grid exception."""

from __future__ import annotations

from icpdf.parser.header_semantics import _is_label_grid
from icpdf.parser.structure import GridCell, TableGrid


def _grid(rows: list[list[str | tuple[str, int, int]]],
          source: str = "rule_lattice") -> TableGrid:
    n_columns = max(len(row) for row in rows)
    xs = [float(index * 100) for index in range(n_columns + 1)]
    ys = [float(index * 10) for index in range(len(rows) + 1)]
    cells: list[GridCell] = []
    for row_index, row in enumerate(rows):
        for column_index, entry in enumerate(row):
            text, row_span, column_span = (
                entry if isinstance(entry, tuple) else (entry, 1, 1))
            cells.append(GridCell(row_index, column_index, row_span,
                                  column_span,
                                  (xs[column_index], ys[row_index],
                                   xs[column_index + 1], ys[row_index + 1]),
                                  text))
    return TableGrid((0.0, 0.0, xs[-1], ys[-1]), xs, ys, cells,
                     source=source)


_DESCRIPTIONS = [
    ["A0", "Dimension designed to accommodate the component width"],
    ["B0", "Dimension designed to accommodate the component length"],
    ["K0", "Dimension designed to accommodate the component thickness"],
    ["W", "Overall width of the carrier tape"],
    ["P1", "Pitch of the component pockets"],
]


def test_taped_dimension_grid_is_a_label_grid():
    assert _is_label_grid(_grid(_DESCRIPTIONS)) is True


def test_prose_rows_are_not_a_label_grid():
    rows = [["This is a sentence about the package drawing", "view"],
            ["Another long sentence that is not a code", "view"],
            ["A third sentence describing the figure", "view"]]
    assert _is_label_grid(_grid(rows)) is False


def test_sparse_drawing_bands_are_not_a_label_grid():
    rows = [["VDD", ""],
            ["GND", "IN"],
            ["OUT", "CLK"],
            ["CLK", "RESET"]]
    assert _is_label_grid(_grid(rows)) is False


def test_text_alignment_grids_are_not_label_grids():
    assert _is_label_grid(_grid(_DESCRIPTIONS, source="text_alignment")) is False


def test_two_short_label_diagram_is_not_a_label_grid():
    """A block diagram of short box labels has no description column."""
    rows = [["VDD", "GND"],
            ["IN", "OUT"],
            ["CLK", "RESET"]]
    assert _is_label_grid(_grid(rows)) is False


def test_leading_cell_must_start_at_column_zero():
    rows = [["", "value", "description text here"],
            ["", "value", "another description"],
            ["", "value", "third description"]]
    assert _is_label_grid(_grid(rows)) is False


def test_merged_leading_cell_is_not_a_label_grid():
    rows = [[("A0", 1, 2), "description text"],
            [("B0", 1, 2), "description text"],
            [("K0", 1, 2), "description text"]]
    assert _is_label_grid(_grid(rows)) is False


def test_two_row_grid_is_not_a_label_grid():
    assert _is_label_grid(_grid(_DESCRIPTIONS[:2])) is False
