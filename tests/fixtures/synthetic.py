# -*- coding: utf-8 -*-
"""Synthetic PDF fixtures for Phase 1. No real datasheets are committed."""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz


def _new_page(doc, *, width: float = 612.0, height: float = 792.0, rotation: int = 0):
    page = doc.new_page(width=width, height=height)
    if rotation:
        page.set_rotation(rotation)
    return page


def _write(page, x: float, y: float, text: str, *, size: float = 10.0,
           rotate: int = 0) -> None:
    page.insert_text((x, y), text, fontsize=size, rotate=rotate)


def simple_three_column(path: Path) -> Path:
    doc = fitz.open()
    page = _new_page(doc)
    for x, text in ((50, "Symbol"), (200, "Min"), (300, "Typ"), (400, "Max")):
        _write(page, x, 100, text)
    rows = (("VOH", "2.4", "3.3", "—"), ("VOL", "0.2", "0.4", "0.6"),
            ("ICC", "1.0", "2.0", "3.0"))
    for index, row in enumerate(rows):
        y = 120 + index * 20
        for x, text in zip((50, 200, 300, 400), row):
            _write(page, x, y, text)
    doc.save(str(path))
    doc.close()
    return path


def duplicate_value_two_tables(path: Path) -> Path:
    doc = fitz.open()
    page = _new_page(doc)
    _write(page, 50, 80, "Recommended Operating Conditions")
    for x, text in ((50, "Symbol"), (200, "Min"), (300, "Typ"), (400, "Max")):
        _write(page, x, 100, text)
    for index, row in enumerate((("VOH", "2.4", "3.3", "—"), ("VOL", "0.1", "0.2", "0.4"))):
        y = 120 + index * 20
        for x, text in zip((50, 200, 300, 400), row):
            _write(page, x, y, text)
    _write(page, 50, 240, "Absolute Maximum Ratings")
    for x, text in ((50, "Symbol"), (200, "Min"), (300, "Typ"), (400, "Max")):
        _write(page, x, 260, text)
    for index, row in enumerate((("VOH", "3.3", "—", "3.6"), ("VOL", "—", "0.2", "0.5"))):
        y = 280 + index * 20
        for x, text in zip((50, 200, 300, 400), row):
            _write(page, x, y, text)
    doc.save(str(path))
    doc.close()
    return path


def incomplete_table(path: Path) -> Path:
    doc = fitz.open()
    page = _new_page(doc)
    for x, text in ((50, "Symbol"), (200, "Min"), (300, "Typ"), (400, "Max")):
        _write(page, x, 100, text)
    for x, text in zip((50, 200, 300, 400), ("VOH", "2.4", "3.3", "—")):
        _write(page, x, 120, text)
    for x, text in ((50, "VOL"), (200, "0.2")):
        _write(page, x, 140, text)
    doc.save(str(path))
    doc.close()
    return path


def rotated_text(path: Path) -> Path:
    doc = fitz.open()
    page = _new_page(doc)
    _write(page, 100, 300, "ROTATED PARAMETER", rotate=90)
    doc.save(str(path))
    doc.close()
    return path


def rotated_page(path: Path) -> Path:
    doc = fitz.open()
    page = _new_page(doc, rotation=90)
    for x, text in ((50, "Symbol"), (200, "Min"), (300, "Typ")):
        _write(page, x, 100, text)
    for x, text in zip((50, 200, 300), ("VOH", "2.4", "3.3")):
        _write(page, x, 120, text)
    doc.save(str(path))
    doc.close()
    return path


def no_text_layer(path: Path) -> Path:
    doc = fitz.open()
    page = _new_page(doc)
    page.draw_rect(fitz.Rect(50, 50, 400, 300), color=(0, 0, 0), width=1)
    page.draw_line((50, 100), (400, 100), color=(0, 0, 0), width=1)
    doc.save(str(path))
    doc.close()
    return path


def corrupt_pdf(path: Path) -> Path:
    path.write_bytes(b"this is not a pdf")
    return path


def multipage_table(path: Path) -> Path:
    doc = fitz.open()
    for offset in (0, 1):
        page = _new_page(doc)
        _write(page, 50, 80, f"Electrical Characteristics page {offset + 1}")
        for x, text in ((50, "Symbol"), (200, "Min"), (300, "Typ")):
            _write(page, x, 100, text)
        for index, row in enumerate((("VOH", "2.4", "3.3"), ("VOL", "0.1", "0.2"))):
            y = 120 + index * 20
            for x, text in zip((50, 200, 300), row):
                _write(page, x, y, text)
    doc.save(str(path))
    doc.close()
    return path


def multi_mpn(path: Path) -> Path:
    doc = fitz.open()
    page = _new_page(doc)
    _write(page, 50, 80, "Device A electrical characteristics")
    _write(page, 50, 120, "VOH 2.4 3.3")
    _write(page, 50, 180, "Device B electrical characteristics")
    _write(page, 50, 220, "VOH 2.6 3.4")
    doc.save(str(path))
    doc.close()
    return path


def marker_pdf(path: Path, *, rotation: int = 0,
               crop: tuple[float, float, float, float] | None = None) -> Path:
    """One MARKER text at unrotated (100, 100); optional CropBox/rotation."""
    doc = fitz.open()
    page = _new_page(doc, rotation=rotation)
    if crop:
        page.set_cropbox(fitz.Rect(*crop))
    _write(page, 100, 100, "MARKER", size=12)
    doc.save(str(path))
    doc.close()
    return path


def quad_ruled_grid(path: Path, *, rows: int = 5, columns: int = 2,
                    x0: float = 80.0, y0: float = 100.0,
                    cell_width: float = 120.0, cell_height: float = 14.0,
                    diagonal: bool = False) -> Path:
    """A grid whose cells are outlined by stroked quadrilaterals (``qu``).

    The invisible-ruling style of TI tape-dimension tables: each cell is its
    own drawing, so no long horizontal or vertical line exists.
    """
    doc = fitz.open()
    page = _new_page(doc)
    for row in range(rows):
        for column in range(columns):
            left = x0 + column * cell_width
            top = y0 + row * cell_height
            if diagonal and row == 0 and column == 0:
                quad = fitz.Quad(fitz.Point(left, top),
                                 fitz.Point(left + cell_width + 8, top + 6),
                                 fitz.Point(left + 6, top + cell_height + 8),
                                 fitz.Point(left + cell_width, top + cell_height))
            else:
                quad = fitz.Quad(fitz.Point(left, top),
                                 fitz.Point(left + cell_width, top),
                                 fitz.Point(left, top + cell_height),
                                 fitz.Point(left + cell_width, top + cell_height))
            page.draw_quad(quad, color=(0, 0, 0), width=0.6)
            _write(page, left + 3, top + cell_height - 4,
                   f"R{row}C{column}", size=7)
    doc.save(str(path))
    doc.close()
    return path


def stacked_line_sections(path: Path, *, sections: int = 3,
                          x0: float = 60.0, y0: float = 80.0,
                          width: float = 440.0,
                          rows_per_section: int = 3,
                          row_height: float = 18.0, gap: float = 12.0,
                          inner_columns: tuple[float, ...] = (0.45, 0.9),
                          body_size: float = 8.0,
                          gap_caption_size: float | None = None) -> Path:
    """Vertically stacked ruled sections sharing one inner column lattice."""
    doc = fitz.open()
    page = _new_page(doc)
    top = y0
    for section in range(sections):
        if section and gap_caption_size:
            _write(page, x0, top - 3.0, f"Section {section}", size=gap_caption_size)
        bottom = top + rows_per_section * row_height
        for column in inner_columns:
            _write(page, x0 + 4, top + row_height - 5,
                   f"S{section} label {column:.0f}", size=body_size)
            page.draw_line((x0 + width * column, top),
                           (x0 + width * column, bottom),
                           color=(0, 0, 0), width=0.6)
        for row in range(rows_per_section + 1):
            y = top + row * row_height
            page.draw_line((x0, y), (x0 + width, y), color=(0, 0, 0), width=0.6)
        top = bottom + gap
    doc.save(str(path))
    doc.close()
    return path
