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
