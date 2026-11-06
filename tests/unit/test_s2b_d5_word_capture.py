# -*- coding: utf-8 -*-
"""D5: both grid builders retain the words assigned to every flat cell."""

from __future__ import annotations

import pymupdf as fitz

from icpdf.parser.config import TableParams
from icpdf.parser.coords import PageGeometry
from icpdf.parser.layout import PageLayout
from icpdf.parser.rule_primitives import RuleComponent, RuleSegment
from icpdf.parser.structure import TableRegion, recognize_structure
from icpdf.parser.table_detector import detect_tables
from icpdf.parser.text_blocks import TextWord, extract_text_blocks


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


def _word_map(blocks) -> dict[str, TextWord]:
    return {word.word_id: word for block in blocks
            for line in block.lines for word in line.words}


def _assert_cell_ids_match_words(detected, words: dict[str, TextWord]) -> None:
    seen: set[str] = set()
    for row in detected.rows:
        for cell in row.cells:
            assert cell.word_ids
            for word_id in cell.word_ids:
                word = words[word_id]
                cx = (word.bbox[0] + word.bbox[2]) / 2.0
                cy = (word.bbox[1] + word.bbox[3]) / 2.0
                assert cell.bbox[0] - 0.8 <= cx <= cell.bbox[2] + 0.8
                assert cell.bbox[1] - 0.8 <= cy <= cell.bbox[3] + 0.8
                assert word_id not in seen
                seen.add(word_id)
    inside = {
        word_id for word_id, word in words.items()
        if detected.bbox[0] - 0.8 <= (word.bbox[0] + word.bbox[2]) / 2.0
        <= detected.bbox[2] + 0.8
        and detected.bbox[1] - 0.8 <= (word.bbox[1] + word.bbox[3]) / 2.0
        <= detected.bbox[3] + 0.8
    }
    assert seen == inside


def test_detect_tables_bridges_rule_grid_word_ids():
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    xs = (100.0, 250.0, 400.0)
    ys = (100.0, 130.0, 160.0, 190.0)
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]), width=1)
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y), width=1)
    for row, y in enumerate((115.0, 145.0, 175.0)):
        for column, x in enumerate((110.0, 260.0, 410.0)):
            page.insert_text((x, y), f"R{row}C{column}", fontsize=9)
    geometry = PageGeometry.from_page(page, 72.0, 1)
    blocks = extract_text_blocks(page, 1, geometry)
    tables = detect_tables(blocks, 1, TableParams(), page=page,
                           geometry=geometry)
    doc.close()

    assert len(tables) == 1
    table = tables[0]
    assert table.detection_method == "rule_lattice"
    assert table.n_rows == 3
    _assert_cell_ids_match_words(table, _word_map(blocks))


def test_detect_tables_bridges_alignment_grid_word_ids():
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    for row, y in enumerate((100.0, 120.0, 140.0)):
        for column, x in enumerate((100.0, 250.0, 400.0)):
            page.insert_text((x, y), f"R{row}C{column}", fontsize=9)
    geometry = PageGeometry.from_page(page, 72.0, 1)
    blocks = extract_text_blocks(page, 1, geometry)
    tables = detect_tables(blocks, 1, TableParams())
    doc.close()

    assert len(tables) == 1
    table = tables[0]
    assert table.detection_method == "text_alignment"
    assert table.n_rows == 3
    _assert_cell_ids_match_words(table, _word_map(blocks))
