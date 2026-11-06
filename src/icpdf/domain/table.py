"""Table structure: cells, rows and reconstruction status."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import BBox, NonEmptyStr


class TableType(str, Enum):
    """Parser-level hypothesis only. Never a final semantic conclusion."""

    ABSOLUTE_MAXIMUM = "absolute_maximum"
    RECOMMENDED_OPERATING = "recommended_operating"
    ELECTRICAL_CHARACTERISTICS = "electrical_characteristics"
    THERMAL = "thermal"
    PIN_FUNCTIONS = "pin_functions"
    ORDERING_INFORMATION = "ordering_information"
    OTHER = "other"
    UNKNOWN = "unknown"


class ReconstructionStatus(str, Enum):
    RECONSTRUCTED = "reconstructed"
    PARTIAL = "partial"
    UNRESOLVED = "unresolved"


class ExtractionMethod(str, Enum):
    TEXT = "text"
    VECTOR_LINES = "vector_lines"
    TABLE_DETECTOR = "table_detector"
    OCR = "ocr"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class Cell(BaseModel):
    """One cell. `text` is the raw extracted text, never a cleaned substitute."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    cell_id: NonEmptyStr
    row_id: NonEmptyStr
    column_id: int = Field(ge=0)
    text: str
    bbox: BBox
    page_number: int = Field(ge=1)
    extraction_method: ExtractionMethod = ExtractionMethod.UNKNOWN
    raw_tokens: list[str] = Field(default_factory=list)


class TableRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    row_id: NonEmptyStr
    cells: list[Cell] = Field(min_length=1)
    bbox: BBox | None = None

    @model_validator(mode="after")
    def _check_row(self) -> "TableRow":
        columns: set[int] = set()
        for cell in self.cells:
            if cell.row_id != self.row_id:
                raise ValueError("cell.row_id must equal TableRow.row_id")
            if cell.column_id in columns:
                raise ValueError("duplicate column_id within one row")
            columns.add(cell.column_id)
        return self


class HeaderCell(BaseModel):
    """Printed cell that supplied one level of one column's header label.

    Header labels are spread across merged canopies, so the same printed cell
    can back several columns; the per-column reference keeps that visible.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    header_cell_id: NonEmptyStr
    column_id: int = Field(ge=0)
    level: int = Field(ge=0)
    text: str
    bbox: BBox
    page_number: int = Field(ge=1)
    source_cell_id: NonEmptyStr | None = None


class Table(BaseModel):
    """A reconstructed table region.

    Invariants:
    * `page_number` is 1-based; `page_end` (optional) must be >= page_number;
    * every cell page must fall within `[page_number, page_end]`;
    * `row_id` and `cell_id` are unique inside the table;
    * `confidence` is only a parser hint, never evidence of correctness;
    * an unrecoverable table must be `unresolved` and carries an uncertainty reason.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    table_id: NonEmptyStr
    document_id: NonEmptyStr
    page_number: int = Field(ge=1)
    page_end: int | None = None
    bbox: BBox
    title: str | None = None
    table_type: TableType = TableType.UNKNOWN
    headers: list[str] = Field(default_factory=list)
    header_rows: int = Field(default=0, ge=0)
    # Per column, the top-to-bottom header labels that produced ``headers``.
    header_path: list[list[str]] = Field(default_factory=list)
    # Cell-level backing for ``header_path``; empty for headerless tables.
    header_cells: list[HeaderCell] = Field(default_factory=list)
    rows: list[TableRow] = Field(default_factory=list)
    detection_method: NonEmptyStr
    confidence: float = Field(ge=0.0, le=1.0)
    reconstruction_status: ReconstructionStatus
    uncertainty_reason: str | None = None
    # Physical ruling components aggregated into this region, and how its
    # outer boundary was obtained: ruled | implied_horizontal |
    # implied_alignment | mixed.
    region_components: list[int] = Field(default_factory=list)
    boundary_source: NonEmptyStr = "ruled"
    merge_evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_table(self) -> "Table":
        if self.page_end is not None and self.page_end < self.page_number:
            raise ValueError("page_end must be >= page_number")
        last_page = self.page_end or self.page_number
        row_ids: set[str] = set()
        cell_ids: set[str] = set()
        for row in self.rows:
            if row.row_id in row_ids:
                raise ValueError("duplicate row_id in table")
            row_ids.add(row.row_id)
            for cell in row.cells:
                if cell.cell_id in cell_ids:
                    raise ValueError("duplicate cell_id in table")
                cell_ids.add(cell.cell_id)
                if not (self.page_number <= cell.page_number <= last_page):
                    raise ValueError("cell.page_number outside table page range")
        header_ids: set[str] = set()
        for header in self.header_cells:
            if header.header_cell_id in header_ids:
                raise ValueError("duplicate header_cell_id in table")
            header_ids.add(header.header_cell_id)
            if header.level >= self.header_rows:
                raise ValueError("header cell level outside header_rows")
            if self.headers and header.column_id >= len(self.headers):
                raise ValueError("header cell column outside headers")
            if not (self.page_number <= header.page_number <= last_page):
                raise ValueError("header cell page outside table page range")
        if self.reconstruction_status is ReconstructionStatus.UNRESOLVED:
            if not self.uncertainty_reason:
                raise ValueError("unresolved table must carry uncertainty_reason")
        return self
