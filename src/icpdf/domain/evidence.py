"""Evidence records that can be resolved back to a PDF page and location."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import BBox, NonEmptyStr, Sha256Hex, finish_non_empty


class EvidenceType(str, Enum):
    CELL_TEXT = "cell_text"
    TABLE_ROW = "table_row"
    PARAGRAPH = "paragraph"
    PAGE_IMAGE = "page_image"
    MANUAL = "manual"


class Evidence(BaseModel):
    """A verifiable pointer into the source PDF.

    Base fields are `document_sha256 + page_number + bbox + raw_text`.
    Table/cell IDs are optional so paragraph-level evidence can exist, but
    `cell_text` / `table_row` evidence must provide all three IDs.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: NonEmptyStr
    document_sha256: Sha256Hex
    page_number: int = Field(ge=1)
    table_id: NonEmptyStr | None = None
    row_id: NonEmptyStr | None = None
    cell_id: NonEmptyStr | None = None
    bbox: BBox
    raw_text: NonEmptyStr
    screenshot_reference: str | None = None
    evidence_type: EvidenceType = EvidenceType.CELL_TEXT

    @model_validator(mode="after")
    def _check_evidence(self) -> "Evidence":
        finish_non_empty(self.raw_text, "raw_text")
        if self.screenshot_reference is not None:
            finish_non_empty(self.screenshot_reference, "screenshot_reference")
        if self.evidence_type in (EvidenceType.CELL_TEXT, EvidenceType.TABLE_ROW):
            if not (self.table_id and self.row_id and self.cell_id):
                raise ValueError(
                    f"{self.evidence_type.value} evidence requires table_id/row_id/cell_id"
                )
        return self
