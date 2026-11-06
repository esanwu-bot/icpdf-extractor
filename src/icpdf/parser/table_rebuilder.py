"""Convert detected layouts into the frozen Table/Cell domain model."""

from __future__ import annotations

from icpdf.domain.table import (
    Cell,
    ExtractionMethod,
    HeaderCell,
    ReconstructionStatus,
    Table,
    TableRow,
)
from icpdf.parser.table_detector import DetectedTable


def build_table(detected: DetectedTable, document_id: str, table_index: int) -> Table:
    table_id = f"p{detected.page_number:03d}-t{table_index:02d}"
    rows: list[TableRow] = []
    row_ids_by_grid_row: dict[int, str] = {}
    for row_index, detected_row in enumerate(detected.rows, 1):
        row_id = f"{table_id}-r{row_index:02d}"
        row_ids_by_grid_row[detected_row.grid_row] = row_id
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
        rows.append(TableRow(row_id=row_id, cells=cells, bbox=detected_row.bbox))
    header_cells: list[HeaderCell] = []
    for ref in detected.header_cells:
        source_row_id = row_ids_by_grid_row.get(ref.source_row)
        header_cells.append(HeaderCell(
            header_cell_id=f"{table_id}-h{ref.level:02d}-c{ref.column:02d}",
            column_id=ref.column,
            level=ref.level,
            text=ref.text,
            bbox=ref.bbox,
            page_number=detected.page_number,
            source_cell_id=(f"{source_row_id}-c{ref.source_column:02d}"
                            if source_row_id else None),
        ))
    return Table(
        table_id=table_id,
        document_id=document_id,
        page_number=detected.page_number,
        bbox=detected.bbox,
        title=detected.title,
        table_type=detected.table_type,          # parser hypothesis only
        headers=detected.headers,
        header_rows=detected.header_rows,
        header_path=detected.header_path,
        header_cells=header_cells,
        rows=rows,
        detection_method=detected.detection_method,
        confidence=detected.confidence,
        reconstruction_status=detected.reconstruction_status,
        uncertainty_reason=detected.uncertainty_reason,
        region_components=detected.region_components,
        boundary_source=detected.boundary_source,
        merge_evidence=detected.merge_evidence,
        visual_boundaries=list(detected.visual_boundaries),
        visual_boundary_status=detected.visual_boundary_status,
        visual_columns=detected.visual_columns,
        partial_boundaries=list(detected.partial_boundaries),
        visual_boundary_evidence=list(detected.visual_boundary_evidence),
    )
