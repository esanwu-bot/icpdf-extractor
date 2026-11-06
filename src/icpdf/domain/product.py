"""Product identity: requested MPN and PDF-observed MPN are separate facts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import BBox, NonEmptyStr


class IdentityScope(str, Enum):
    DEVICE = "device"
    BOARD = "board"
    ONBOARD_DEVICE = "onboard_device"
    UNKNOWN = "unknown"


class ProductType(str, Enum):
    IC = "ic"
    BOARD = "board"
    MODULE = "module"
    UNKNOWN = "unknown"


class IdentityEvidence(BaseModel):
    """One observation that supports (or challenges) the product identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: NonEmptyStr
    page_number: int = Field(ge=1)
    raw_text: NonEmptyStr
    bbox: BBox | None = None


class Product(BaseModel):
    """A product instance inside one document.

    `requested_mpn` is what the caller asked for. `normalized_mpn` is what the
    document actually supports. They must never overwrite each other.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    product_id: NonEmptyStr
    document_id: NonEmptyStr
    requested_mpn: NonEmptyStr
    normalized_mpn: NonEmptyStr
    identity_scope: IdentityScope = IdentityScope.UNKNOWN
    product_type: ProductType = ProductType.UNKNOWN
    manufacturer: str | None = None
    package: str | None = None
    identity_evidence: list[IdentityEvidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_product(self) -> "Product":
        if self.normalized_mpn.casefold() == self.requested_mpn.casefold():
            return self
        if not self.identity_evidence:
            raise ValueError(
                "normalized_mpn differs from requested_mpn; identity_evidence is required"
            )
        return self
