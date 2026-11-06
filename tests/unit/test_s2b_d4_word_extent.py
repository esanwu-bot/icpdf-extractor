# -*- coding: utf-8 -*-
"""D4: word centers must stay inside the outer logical extent."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from icpdf.parser.structure import (
    LogicalMappingError,
    assign_words_to_logical_columns,
)


@dataclass(frozen=True)
class _Word:
    word_id: str
    bbox: tuple[float, float, float, float]


def _word(word_id: str, cx: float, width: float = 10.0,
          y: float = 10.0) -> _Word:
    return _Word(word_id, (cx - width / 2.0, y, cx + width / 2.0, y + 8.0))


BOUNDARIES = (0.0, 100.0, 200.0)


def test_outer_edges_are_inside_and_internal_ties_go_left():
    result = assign_words_to_logical_columns(
        [_word("left", 0.0), _word("mid", 50.0), _word("tie", 100.0),
         _word("right", 200.0)],
        BOUNDARIES,
    )
    assert result.columns == {"left": 0, "mid": 0, "tie": 0, "right": 1}
    assert result.boundary_ties == ("left", "tie", "right")


def test_left_outside_is_unresolved():
    with pytest.raises(LogicalMappingError) as exc:
        assign_words_to_logical_columns([_word("left", -0.01)], BOUNDARIES)
    assert exc.value.reason_code == "mapping_word_outside_logical_extent"
    assert exc.value.word_id == "left"


def test_right_outside_is_unresolved():
    with pytest.raises(LogicalMappingError) as exc:
        assign_words_to_logical_columns([_word("right", 200.01)], BOUNDARIES)
    assert exc.value.reason_code == "mapping_word_outside_logical_extent"
    assert exc.value.word_id == "right"


def test_outside_word_is_never_clamped_to_an_outer_column():
    with pytest.raises(LogicalMappingError) as exc:
        assign_words_to_logical_columns([_word("far", 500.0)], BOUNDARIES)
    assert exc.value.reason_code == "mapping_word_outside_logical_extent"


def test_non_finite_center_is_not_assigned():
    with pytest.raises(LogicalMappingError) as exc:
        assign_words_to_logical_columns([_word("inf", float("inf"))], BOUNDARIES)
    assert exc.value.reason_code == "mapping_word_not_assigned"


def test_boundaries_must_be_strictly_ascending():
    with pytest.raises(ValueError):
        assign_words_to_logical_columns([], (0.0, 0.0, 100.0))
