"""Convert detected layouts into the frozen Table/Cell domain model."""

from __future__ import annotations

from icpdf.domain.table import (
    Cell,
    ExtractionMethod,
    ReconstructionStatus,
    Table,
    TableRow,
)
from icpdf.parser.table_detector import DetectedTable


def build_table(detected: DetectedTable, document_id: str, table_index: int) -> Table:
    table_id = f"p{detected.page_number:03d}-t{table_index:02d}"
    rows: list[TableRow] = []
    for row_index, detected_row in enumerate(detected.rows, 1):
        row_id = f"{table_id}-r{row_index:02d}"
        cells: list[Cell] = []
        seen_columns: set[int] = set()
        for cell in detected_row.cells:
            column = cell.column_index
            while column in seen_columns:                     # keep IDs unique on ragged rows
                column += 1
            seen_columns.add(column)
            cells.append(Cell(
                cell_id=f"{row_id}-c{column:02d}",
                row_id=row_id,
                column_id=column,
                text=cell.text,
                bbox=cell.bbox,
                page_number=detected.page_number,
                extraction_method=ExtractionMethod.TABLE_DETECTOR,
                raw_tokens=cell.text.split(),
            ))
        rows.append(TableRow(row_id=row_id, cells=cells))
    return Table(
        table_id=table_id,
        document_id=document_id,
        page_number=detected.page_number,
        bbox=detected.bbox,
        title=detected.title,
        table_type=detected.table_type,          # parser hypothesis only
        headers=detected.headers,
        rows=rows,
        detection_method="text_alignment",
        confidence=detected.confidence,
        reconstruction_status=detected.reconstruction_status,
        uncertainty_reason=detected.uncertainty_reason,
    )
