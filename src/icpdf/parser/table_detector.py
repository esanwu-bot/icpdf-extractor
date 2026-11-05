"""Table detector orchestration.

The detector is intentionally thin: it runs the five layers and assembles their
output.  Decisions live in:

1. :mod:`icpdf.parser.layout`           - page layout analysis
2. :mod:`icpdf.parser.table_regions`    - table region detection
3. :mod:`icpdf.parser.structure`        - row/column structure recognition
4. :mod:`icpdf.parser.header_semantics` - headers, column roles, table type
5. :mod:`icpdf.parser.candidate_registry` - candidate registry (after rebuild)
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from icpdf.domain.common import BBox
from icpdf.domain.table import ReconstructionStatus, TableType
from icpdf.parser.config import TableParams
from icpdf.parser.header_semantics import assess_region, infer_semantics
from icpdf.parser.layout import analyze_layout
from icpdf.parser.structure import TableGrid, recognize_structure
from icpdf.parser.table_regions import detect_table_regions
from icpdf.parser.text_blocks import TextBlock


class DetectedCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    text: str
    bbox: BBox
    column_index: int = Field(ge=0)
    row_span: int = Field(default=1, ge=1)
    column_span: int = Field(default=1, ge=1)


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
    header_rows: int = Field(default=0, ge=0)
    header_path: list[list[str]] = Field(default_factory=list)
    column_roles: list[str] = Field(default_factory=list)
    rows: list[DetectedRow] = Field(default_factory=list)
    detection_method: str = "text_alignment"
    confidence: float = Field(ge=0.0, le=1.0)
    reconstruction_status: ReconstructionStatus
    uncertainty_reason: str | None = None


def _ragged_rows(grid: TableGrid, header_rows: int) -> list[int]:
    """Data rows whose populated column coverage is below the table maximum."""
    coverage: list[set[int]] = [set() for _ in range(grid.n_rows)]
    for cell in grid.cells:
        if not cell.text.strip():
            continue
        for row in range(cell.row, min(cell.row + cell.row_span, grid.n_rows)):
            coverage[row].update(range(cell.column, cell.column + cell.column_span))
    populated = [len(columns) for columns in coverage[header_rows:] if columns]
    if not populated:
        return []
    expected = max(populated)
    return [header_rows + index for index, columns in enumerate(coverage[header_rows:])
            if columns and len(columns) < expected]


def _status(grid: TableGrid, layout_source: str, header_rows: int,
            unassigned: int) -> tuple[ReconstructionStatus, str | None, float]:
    if header_rows == 0:
        return (ReconstructionStatus.PARTIAL,
                "no header row detected; table retained from structural evidence",
                0.55)
    ragged = _ragged_rows(grid, header_rows)
    if ragged:
        return (ReconstructionStatus.PARTIAL,
                f"{len(ragged)} data row(s) are missing cells; structure is incomplete",
                0.6)
    if unassigned:
        return (ReconstructionStatus.PARTIAL,
                f"{unassigned} words inside the region were not assignable to cells",
                0.6)
    confidence = 0.9 if layout_source == "rule_lattice" else 0.65
    return ReconstructionStatus.RECONSTRUCTED, None, confidence


def detect_tables(blocks: list[TextBlock], page_number: int,
                  params: TableParams | None = None, *,
                  page=None, geometry=None) -> list[DetectedTable]:
    params = params or TableParams()
    layout = analyze_layout(
        page, blocks, page_number, geometry=geometry,
        min_rule_width=params.rule_min_width_pt,
        min_rule_height=params.rule_min_height_pt,
    )
    detected: list[DetectedTable] = []
    for region in detect_table_regions(layout, params):
        grid = recognize_structure(layout, region, params)
        if not grid.cells:
            continue
        semantics = infer_semantics(layout, region, grid, params)
        accepted, reason = assess_region(grid, semantics, params)
        if not accepted:
            continue

        rows: list[DetectedRow] = []
        for row_index in range(grid.n_rows):
            cells = [DetectedCell(
                text=cell.text,
                bbox=cell.bbox,
                column_index=cell.column,
                row_span=cell.row_span,
                column_span=cell.column_span,
            ) for cell in grid.cells
                if cell.row == row_index and cell.text.strip()]
            if not cells:
                continue
            bbox = (min(cell.bbox[0] for cell in cells), min(cell.bbox[1] for cell in cells),
                    max(cell.bbox[2] for cell in cells), max(cell.bbox[3] for cell in cells))
            rows.append(DetectedRow(bbox=bbox, cells=cells))
        if not rows:
            continue

        status, uncertainty, confidence = _status(
            grid, region.source, semantics.header_rows, len(grid.unassigned_words))
        detected.append(DetectedTable(
            page_number=page_number,
            bbox=region.bbox,
            title=semantics.title,
            table_type=semantics.table_type,
            headers=semantics.headers,
            header_rows=semantics.header_rows,
            header_path=semantics.header_path,
            column_roles=[role.value for role in semantics.column_roles],
            rows=rows,
            detection_method=region.source,
            confidence=confidence,
            reconstruction_status=status,
            uncertainty_reason=uncertainty,
        ))
    return detected
