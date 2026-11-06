"""Visual boundary lattice: printed vertical separators of one table region.

This is a derived, read-only view over the physical ruling.  It never replaces
or renumbers the recognition lattice (`TableGrid.xs`, cell ids, bboxes).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# outer_left | outer_right | internal
VISUAL_BOUNDARY_ROLES = ("outer_left", "outer_right", "internal")
VISUAL_BOUNDARY_STATUSES = ("printed", "partial", "implied_outer", "not_printed")


class VisualSegment(BaseModel):
    """One clipped vertical rule segment behind a visual boundary.

    ``component_id`` is the :class:`RuleComponent` the segment came from and
    ``primitive_indices`` indexes the page-level ``collect_primitives`` list,
    so a boundary can be walked back to its ruling primitives.  ``y0``/``y1``
    are clipped to the table region and are the inputs of the coverage
    recomputation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    component_id: int
    y0: float
    y1: float
    primitive_indices: list[int] = Field(default_factory=list)


class VisualBoundary(BaseModel):
    """One visual separator, with the evidence that produced it.

    ``drawn`` is true when a printed vertical rule exists at this position;
    an outer edge may be implied by the region's horizontal-rule extent.
    ``coverage`` is the unioned rule length clipped to the region height,
    divided by that height (0 for an implied edge).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    x: float
    role: str
    drawn: bool
    coverage: float = Field(ge=0.0, le=1.0)
    component_ids: list[int] = Field(default_factory=list)
    segment_count: int = Field(default=0, ge=0)
    segments: list[VisualSegment] = Field(default_factory=list)


__all__ = ["VISUAL_BOUNDARY_ROLES", "VISUAL_BOUNDARY_STATUSES",
           "VisualBoundary", "VisualSegment"]
