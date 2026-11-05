"""Candidate registry entries: every candidate is bound to table/row/cell/page/bbox."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import BBox, NonEmptyStr
from .table import ExtractionMethod, ReconstructionStatus


class ColumnRole(str, Enum):
    MIN = "min"
    TYP = "typ"
    MAX = "max"
    VALUE = "value"
    CONDITION = "condition"
    UNIT = "unit"
    SYMBOL = "symbol"
    UNKNOWN = "unknown"


class CandidateType(str, Enum):
    PARAMETER_NAME = "parameter_name"
    VALUE = "value"
    UNIT = "unit"
    CONDITION = "condition"
    SYMBOL = "symbol"
    ROW_LABEL = "row_label"
    OTHER = "other"


class SourceTextType(str, Enum):
    """Keep native PDF text and OCR guesses strictly separated."""

    NATIVE_PDF_TEXT = "native_pdf_text"
    OCR = "ocr"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class Candidate(BaseModel):
    """One raw value observed in one cell.

    `candidate_id` must be unique within a run. A number appearing in two
    different tables yields two candidates, never one merged candidate.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: NonEmptyStr
    document_id: NonEmptyStr
    table_id: NonEmptyStr
    row_id: NonEmptyStr
    cell_id: NonEmptyStr
    page_number: int = Field(ge=1)
    bbox: BBox
    raw_text: NonEmptyStr
    normalized_value: str | None = None
    unit: str | None = None
    column_role: ColumnRole = ColumnRole.UNKNOWN
    candidate_type: CandidateType = CandidateType.VALUE
    #: How this cell was obtained. `source_text_type` must never be upgraded
    #: silently: OCR text stays OCR text.
    extraction_method: ExtractionMethod = ExtractionMethod.UNKNOWN
    source_text_type: SourceTextType = SourceTextType.UNKNOWN
    reconstruction_status: ReconstructionStatus = ReconstructionStatus.RECONSTRUCTED


class CandidateSet(BaseModel):
    """Immutable candidate snapshot for one run of one document."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: NonEmptyStr
    document_id: NonEmptyStr
    candidates: list[Candidate] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_set(self) -> "CandidateSet":
        ids: set[str] = set()
        for candidate in self.candidates:
            if candidate.candidate_id in ids:
                raise ValueError(f"duplicate candidate_id: {candidate.candidate_id}")
            ids.add(candidate.candidate_id)
            if candidate.document_id != self.document_id:
                raise ValueError(
                    "candidate from another document: "
                    f"{candidate.document_id} != {self.document_id}"
                )
        return self
