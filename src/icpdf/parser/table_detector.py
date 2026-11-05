"""Deterministic table detection from native text lines.

This is a conservative detector: it only claims a table when multiple lines
share a stable column layout. Anything else is reported with an uncertainty
reason instead of being guessed.
"""

from __future__ import annotations

import statistics
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from icpdf.domain.common import BBox
from icpdf.domain.table import ReconstructionStatus, TableType
from icpdf.parser.text_blocks import TextBlock, TextLine

#: Two words belong to different columns when the horizontal gap exceeds this.
CELL_GAP_PT = 8.0
#: A table ends when the vertical gap exceeds this many median line heights.
ROW_GAP_FACTOR = 2.5

_HEADER_WORDS = {
    "symbol", "parameter", "min", "minimum", "typ", "typical", "max", "maximum",
    "unit", "units", "condition", "conditions", "test", "value", "limit", "limits",
}

_TYPE_KEYWORDS: tuple[tuple[TableType, tuple[str, ...]], ...] = (
    (TableType.ABSOLUTE_MAXIMUM, ("absolute maximum", "absolute max")),
    (TableType.RECOMMENDED_OPERATING, ("recommended operating", "recommended operation")),
    (TableType.ELECTRICAL_CHARACTERISTICS, ("electrical characteristics", "electrical spec")),
    (TableType.THERMAL, ("thermal", "thermal resistance")),
    (TableType.PIN_FUNCTIONS, ("pin function", "pin configuration", "pin description")),
    (TableType.ORDERING_INFORMATION, ("ordering information", "orderable")),
)


class DetectedCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    text: str
    bbox: BBox
    column_index: int = Field(ge=0)


class DetectedRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    bbox: BBox
    cells: list[DetectedCell]


class DetectedTable(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    page_number: int = Field(ge=1)
    bbox: BBox
    title: str | None = None
    table_type: TableType = TableType.UNKNOWN
    headers: list[str] = Field(default_factory=list)
    rows: list[DetectedRow] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    reconstruction_status: ReconstructionStatus
    uncertainty_reason: str | None = None


def _split_cells(words: list) -> list[DetectedCell]:
    words = sorted(words, key=lambda w: w.bbox[0])
    groups: list[list] = []
    for word in words:
        if groups and word.bbox[0] - groups[-1][-1].bbox[2] <= CELL_GAP_PT:
            groups[-1].append(word)
        else:
            groups.append([word])
    cells: list[DetectedCell] = []
    for index, group in enumerate(groups):
        cells.append(DetectedCell(
            text=" ".join(w.text for w in group).strip(),
            bbox=(min(w.bbox[0] for w in group), min(w.bbox[1] for w in group),
                  max(w.bbox[2] for w in group), max(w.bbox[3] for w in group)),
            column_index=index,
        ))
    return cells


def _collect_rows(blocks: list[TextBlock]) -> list[list]:
    """Group words by horizontal baseline, not by PyMuPDF block/line objects.

    Builders often emit one text object per cell, so a visual table row can span
    many PDF lines/spans. Baseline clustering is what makes the row coherent.
    """
    words = [w for block in blocks for line in block.lines for w in line.words]
    if not words:
        return []
    heights = [w.bbox[3] - w.bbox[1] for w in words if w.bbox[3] > w.bbox[1]]
    median_h = statistics.median(heights) if heights else 10.0
    tolerance = max(3.0, median_h * 0.5)
    words.sort(key=lambda w: ((w.bbox[1] + w.bbox[3]) / 2.0, w.bbox[0]))
    rows: list[list] = []
    centers: list[float] = []
    for word in words:
        center = (word.bbox[1] + word.bbox[3]) / 2.0
        if rows and abs(center - centers[-1]) <= tolerance:
            rows[-1].append(word)
            centers[-1] = sum((w.bbox[1] + w.bbox[3]) / 2.0 for w in rows[-1]) / len(rows[-1])
        else:
            rows.append([word])
            centers.append(center)
    return [sorted(row, key=lambda w: w.bbox[0]) for row in rows]


def _median_line_height(lines: list[TextLine]) -> float:
    heights = [l.bbox[3] - l.bbox[1] for l in lines if l.bbox[3] > l.bbox[1]]
    return statistics.median(heights) if heights else 10.0


def _header_score(cells: list[DetectedCell]) -> int:
    hits = 0
    for cell in cells:
        token = cell.text.casefold().strip(" .:")
        if token in _HEADER_WORDS or any(h in token for h in _HEADER_WORDS):
            hits += 1
    return hits


def _infer_type(title: str | None, headers: list[str], header_row: str) -> TableType:
    haystack = " ".join(x for x in (title or "", " ".join(headers), header_row) if x).casefold()
    for table_type, keywords in _TYPE_KEYWORDS:
        if any(k in haystack for k in keywords):
            return table_type
    return TableType.UNKNOWN


def _bbox_union(boxes: list[BBox]) -> BBox:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _can_extend(table_rows: list[DetectedRow], rows_box: BBox,
                cells: list[DetectedCell], last_bottom: float,
                median_h: float) -> bool:
    modal = statistics.mode([len(r.cells) for r in table_rows]) if table_rows else len(cells)
    if abs(len(cells) - modal) > 2 or len(cells) < 2:
        return False
    row_box = (min(c.bbox[0] for c in cells), min(c.bbox[1] for c in cells),
               max(c.bbox[2] for c in cells), max(c.bbox[3] for c in cells))
    overlap = min(rows_box[2], row_box[2]) - max(rows_box[0], row_box[0])
    if overlap <= 0:
        return False
    gap = row_box[1] - last_bottom
    return gap <= ROW_GAP_FACTOR * median_h


def detect_tables(blocks: list[TextBlock], page_number: int) -> list[DetectedTable]:
    rows_words = _collect_rows(blocks)
    if not rows_words:
        return []
    heights = [w.bbox[3] - w.bbox[1] for row in rows_words for w in row
               if w.bbox[3] > w.bbox[1]]
    median_h = statistics.median(heights) if heights else 10.0
    tables: list[DetectedTable] = []
    current: list[DetectedRow] = []
    pending_title: str | None = None
    last_bottom = 0.0

    def close_current() -> None:
        nonlocal current, pending_title
        if not current:
            return
        cells_per_row = [len(r.cells) for r in current]
        modal = statistics.mode(cells_per_row)
        if len(current) < 2:
            status = ReconstructionStatus.UNRESOLVED
            reason = "fewer than two rows; cannot prove a table"
            confidence = 0.0
        elif any(c != modal for c in cells_per_row):
            status = ReconstructionStatus.PARTIAL
            reason = f"ragged rows: column counts {cells_per_row} vs modal {modal}"
            confidence = 0.5
        else:
            status = ReconstructionStatus.RECONSTRUCTED
            reason = None
            confidence = 0.9
        header_row = current[0]
        headers = [c.text for c in header_row.cells] if _header_score(header_row.cells) >= 2 else []
        rows = current[1:] if headers else current
        title = pending_title
        if title is None and headers:
            title = " / ".join(headers)
        table_type = _infer_type(title, headers,
                                 " ".join(c.text for c in header_row.cells))
        if rows:
            tables.append(DetectedTable(
                page_number=page_number,
                bbox=_bbox_union([r.bbox for r in rows]),
                title=title, table_type=table_type, headers=headers, rows=rows,
                confidence=confidence, reconstruction_status=status,
                uncertainty_reason=reason,
            ))
        current = []
        pending_title = None

    for words in rows_words:
        cells = _split_cells(words)
        line_bbox = (min(w.bbox[0] for w in words), min(w.bbox[1] for w in words),
                     max(w.bbox[2] for w in words), max(w.bbox[3] for w in words))
        line_text = " ".join(w.text for w in words).strip()
        if len(cells) < 2:
            close_current()
            if line_text and len(line_text) <= 120:
                pending_title = line_text
            last_bottom = line_bbox[3]
            continue
        if current:
            rows_box = _bbox_union([r.bbox for r in current])
            if not _can_extend(current, rows_box, cells, last_bottom, median_h):
                close_current()
        current.append(DetectedRow(
            bbox=(min(c.bbox[0] for c in cells), min(c.bbox[1] for c in cells),
                  max(c.bbox[2] for c in cells), max(c.bbox[3] for c in cells)),
            cells=cells,
        ))
        last_bottom = line_bbox[3]
    close_current()
    return tables
