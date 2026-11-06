"""Document identity: one immutable PDF artifact and its parser context."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import NonEmptyStr, Sha256Hex


class DocumentType(str, Enum):
    DATASHEET = "datasheet"
    USER_GUIDE = "user_guide"
    QUICK_START = "quick_start"
    ERRATA = "errata"
    UNKNOWN = "unknown"


class Document(BaseModel):
    """A source PDF. Identity is `sha256`, not filename.

    Invariants:
    * `page_count >= 1`;
    * `created_at` must be timezone-aware;
    * if page sizes/rotations are supplied they must cover every page;
    * no mutable "current status" fields: a Document is immutable input evidence.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: NonEmptyStr
    filename: NonEmptyStr
    sha256: Sha256Hex
    page_count: int = Field(ge=1)
    source_uri: str | None = None
    manufacturer: str | None = None
    document_title: str | None = None
    document_type: DocumentType = DocumentType.UNKNOWN
    parser_version: NonEmptyStr
    created_at: datetime
    #: `(width, height)` in PDF points, origin top-left, unit = 1/72 inch.
    page_sizes: list[tuple[float, float]] = Field(default_factory=list)
    page_rotations: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_document(self) -> "Document":
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.page_sizes and len(self.page_sizes) != self.page_count:
            raise ValueError("page_sizes must cover every page")
        if self.page_rotations and len(self.page_rotations) != self.page_count:
            raise ValueError("page_rotations must cover every page")
        for width, height in self.page_sizes:
            if width <= 0 or height <= 0:
                raise ValueError("page size must be positive")
        for rotation in self.page_rotations:
            if rotation % 90 != 0:
                raise ValueError("page rotation must be a multiple of 90 degrees")
        return self
