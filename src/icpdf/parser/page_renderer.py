"""Render a PDF page to PNG and keep the point↔pixel mapping explicit."""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz

from icpdf.parser.coords import PageGeometry
from icpdf.parser.pdf_loader import PDFLoadError


def render_page(pdf_path: str | Path, page_number: int, out_path: str | Path,
                *, dpi: float = 150.0) -> PageGeometry:
    """Render one 1-based page. Returns the geometry used for the PNG."""
    pdf_path = Path(pdf_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with fitz.open(str(pdf_path)) as doc:
            if page_number < 1 or page_number > doc.page_count:
                raise PDFLoadError(f"page {page_number} outside 1..{doc.page_count}")
            page = doc[page_number - 1]
            effective_dpi = int(round(dpi))
            pix = page.get_pixmap(dpi=effective_dpi, alpha=False)
            pix.save(str(out_path))
            return PageGeometry.from_page(page, dpi=float(effective_dpi),
                                          page_number=page_number)
    except PDFLoadError:
        raise
    except Exception as exc:                                   # noqa: BLE001
        raise PDFLoadError(f"render failed: {type(exc).__name__}: {exc}") from exc
