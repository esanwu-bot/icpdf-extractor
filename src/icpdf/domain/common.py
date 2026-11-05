"""Shared constrained scalar types for the domain contract."""

from __future__ import annotations

from typing import Annotated, TypeAlias

from pydantic import AfterValidator, StringConstraints

#: Lower-case SHA-256 hex digest. Evidence is bound to a document by this value,
#: never by filename (filenames are not stable across re-downloads).
Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]

#: Non-empty, whitespace-stripped identifier / label.
NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]

BBoxTuple: TypeAlias = tuple[float, float, float, float]


def _bbox_is_ordered(value: BBoxTuple) -> BBoxTuple:
    x0, y0, x1, y1 = value
    if x1 < x0 or y1 < y0:
        raise ValueError("bbox must satisfy x1 >= x0 and y1 >= y0")
    return value


#: `(x0, y0, x1, y1)` in PDF page space (origin top-left, unit = point).
BBox = Annotated[BBoxTuple, AfterValidator(_bbox_is_ordered)]


def finish_non_empty(value: str, field: str = "value") -> str:
    """Reject strings that are visually empty (spaces-only)."""
    if not value.strip():
        raise ValueError(f"{field} must not be blank")
    return value
