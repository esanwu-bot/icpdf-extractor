"""Visual boundary lattice: printed vertical separators of one table region.

This is a derived, read-only view over the physical ruling.  It never replaces
or renumbers the recognition lattice (`TableGrid.xs`, cell ids, bboxes).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# outer_left | outer_right | internal
VISUAL_BOUNDARY_ROLES = ("outer_left", "outer_right", "internal")
VISUAL_BOUNDARY_STATUSES = ("printed", "partial", "implied_outer", "not_printed")


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


__all__ = ["VISUAL_BOUNDARY_ROLES", "VISUAL_BOUNDARY_STATUSES",
           "VisualBoundary"]
