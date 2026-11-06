# -*- coding: utf-8 -*-
"""D5: both grid builders retain the words assigned to every flat cell."""

from __future__ import annotations

from icpdf.parser.config import TableParams
from icpdf.parser.layout import PageLayout
from icpdf.parser.rule_primitives import RuleComponent, RuleSegment
from icpdf.parser.structure import TableRegion, recognize_structure
from icpdf.parser.text_blocks import TextWord


def _word(word_id: str, x0: float, y0: float, x1: float,
          y1: float) -> TextWord:
    return TextWord(word_id=word_id, text=word_id, bbox=(x0, y0, x1, y1))


def _layout(words: list[TextWord]) -> PageLayout:
    return PageLayout(page_number=1, rect=(0.0, 0.0, 300.0, 100.0),
                      blocks=[], words=words, row_bands=[], components=[])


def _rule_region() -> TableRegion:
    horizontal = tuple(RuleSegment("h", 0.0, 200.0, y)
                       for y in (0.0, 20.0, 40.0, 60.0))
    vertical = tuple(RuleSegment("v", 0.0, 60.0, x)
                     for x in (0.0, 100.0, 200.0))
    component = RuleComponent((0.0, 0.0, 200.0, 60.0), horizontal, vertical,
                              page_number=1, component_id=0)
    return TableRegion(page_number=1, bbox=(0.0, 0.0, 200.0, 60.0),
                       source="rule_lattice", component=component,
                       components=(component,), boundary_source="ruled")


def _grid_words() -> list[TextWord]:
    words: list[TextWord] = []
    for row, y in enumerate((4.0, 24.0, 44.0)):
        words.append(_word(f"A{row}", 10.0, y, 40.0, y + 10.0))
        words.append(_word(f"B{row}", 110.0, y, 140.0, y + 10.0))
    return words


def test_rule_grid_retains_flat_cell_words():
    words = _grid_words()
    grid = recognize_structure(_layout(words), _rule_region(), TableParams())

    assert len(grid.cells) == 6
    assert set(grid.cell_words) == set(range(6))
    assert [word.word_id for word in grid.cell_words[0]] == ["A0"]
    assert [word.word_id for word in grid.cell_words[1]] == ["B0"]
    assert [word.word_id for word in grid.cell_words[5]] == ["B2"]


def test_alignment_grid_retains_group_words():
    rows = tuple(
        (_word(f"A{row}", 10.0, y, 30.0, y + 10.0),
         _word(f"B{row}", 110.0, y, 130.0, y + 10.0))
        for row, y in enumerate((10.0, 40.0, 70.0))
    )
    words = [word for row in rows for word in row]
    region = TableRegion(page_number=1, bbox=(0.0, 0.0, 300.0, 100.0),
                         source="text_alignment", rows_words=rows,
                         boundary_source="implied_alignment")
    grid = recognize_structure(_layout(words), region, TableParams())

    assert len(grid.cells) == 6
    assert set(grid.cell_words) == set(range(6))
    assert [word.word_id for word in grid.cell_words[0]] == ["A0"]
    assert [word.word_id for word in grid.cell_words[1]] == ["B0"]
    assert [word.word_id for word in grid.cell_words[5]] == ["B2"]
