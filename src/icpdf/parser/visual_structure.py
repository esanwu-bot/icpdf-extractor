"""Layer 3b - visual boundary lattice.

The visual lattice is the set of *printed* vertical separators of an accepted
table region.  It is derived read-only from the region's ruled components and
is deliberately independent of the recognition lattice (``grid.xs``, cell ids,
cell bboxes), which stays frozen.

Status precedence (S2 design r1, section 4.2, clarified per review P1):

* no internal separator                          -> ``not_printed``
* any *internal* separator below full height      -> ``partial``
* every internal separator full, either outer
  edge not fully drawn                            -> ``implied_outer``
* every internal separator full, both outer
  edges fully drawn                               -> ``printed``

An outer edge is drawn when a vertical rule at that x covers at least
:attr:`TableParams.visual_full_height_coverage` of the region height; otherwise
it is implied by the region extent.  A missing outer edge never makes a table
``partial`` on its own: ``partial`` is driven by internal separators only.  A
single implied side is enough for ``implied_outer``; each side keeps its own
drawn/implied evidence.

Determinism: segments are ordered by ``(x, y0, y1, component_id)`` before
grouping, and a group is anchored at its first segment.  A later segment joins
only when it is within ``visual_boundary_tol_pt`` of that anchor, so a chain of
slowly drifting x positions cannot merge into one wide cluster.
"""

from __future__ import annotations

from dataclasses import dataclass

from icpdf.domain.visual import VisualBoundary, VisualSegment
from icpdf.parser.config import TableParams
from icpdf.parser.layout import RuleComponent, RuleSegment
from icpdf.parser.structure import TableRegion


@dataclass(frozen=True)
class VisualStructure:
    boundaries: tuple[VisualBoundary, ...]
    visual_boundaries: tuple[float, ...]
    visual_boundary_status: str
    visual_columns: int | None
    partial_boundaries: tuple[float, ...]
    region_height: float


def _components(region: TableRegion) -> tuple[RuleComponent, ...]:
    if region.components:
        return region.components
    return (region.component,) if region.component is not None else ()


def _union_length(spans: list[tuple[float, float]], tol: float) -> float:
    spans = sorted(span for span in spans if span[0] < span[1])
    if not spans:
        return 0.0
    total = 0.0
    start, end = spans[0]
    for next_start, next_end in spans[1:]:
        if next_start <= end + tol:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    return total + (end - start)


def _group_segments(entries: list[tuple[RuleSegment, RuleComponent]], tol: float
                    ) -> list[tuple[float, list[tuple[RuleSegment, RuleComponent]]]]:
    """Anchor-based grouping, independent of input order after sorting."""
    groups: list[tuple[float, list[tuple[RuleSegment, RuleComponent]]]] = []
    for segment, component in entries:
        if groups and abs(segment.c - groups[-1][0]) <= tol:
            groups[-1][1].append((segment, component))
        else:
            groups.append((segment.c, [(segment, component)]))
    return groups


def _primitive_indices(component: RuleComponent, segment: RuleSegment,
                       tol: float) -> list[int]:
    """Page-level primitive indices that produced ``segment``."""
    indices: set[int] = set()
    for index, primitive in zip(component.primitive_indices, component.primitives):
        if primitive.orientation != "v":
            continue
        if abs(primitive.c - segment.c) > tol:
            continue
        if primitive.a >= segment.b or primitive.b <= segment.a:
            continue
        indices.add(index)
    return sorted(indices)


def build_visual_structure(region: TableRegion,
                           params: TableParams | None = None) -> VisualStructure:
    params = params or TableParams()
    bbox = region.bbox
    x0, x1 = bbox[0], bbox[2]
    y0, y1 = bbox[1], bbox[3]
    height = y1 - y0
    tol = params.visual_boundary_tol_pt
    full = params.visual_full_height_coverage

    entries: list[tuple[RuleSegment, RuleComponent]] = []
    if height > 0:
        for component in _components(region):
            for segment in component.vertical:
                if segment.length < params.visual_min_rule_span_pt:
                    continue
                if not (x0 - tol <= segment.c <= x1 + tol):
                    continue
                entries.append((segment, component))
    entries.sort(key=lambda entry: (entry[0].c, entry[0].a, entry[0].b,
                                   entry[1].component_id))
    groups = _group_segments(entries, tol) if height > 0 else []

    left, right, internal = [], [], []
    for _anchor, members in groups:
        position = sum(segment.c for segment, _ in members) / len(members)
        spans: list[tuple[float, float]] = []
        segments: list[VisualSegment] = []
        for segment, component in members:
            start, end = max(y0, segment.a), min(y1, segment.b)
            if end <= start:
                continue
            spans.append((start, end))
            segments.append(VisualSegment(
                component_id=component.component_id,
                y0=start,
                y1=end,
                primitive_indices=_primitive_indices(component, segment, tol),
            ))
        coverage = _union_length(spans, tol) / height
        entry = (position, segments, coverage)
        if abs(position - x0) <= tol:
            left.append(entry)
        elif abs(position - x1) <= tol:
            right.append(entry)
        elif x0 + tol < position < x1 - tol:
            internal.append(entry)

    def _outer(candidates, x: float, role: str) -> VisualBoundary:
        if not candidates:
            return VisualBoundary(x=x, role=role, drawn=False, coverage=0.0)
        _, segments, coverage = max(candidates, key=lambda item: item[2])
        return VisualBoundary(x=x, role=role, drawn=coverage >= full,
                              coverage=min(1.0, coverage),
                              component_ids=sorted({s.component_id
                                                    for s in segments}),
                              segment_count=len(segments),
                              segments=segments)

    boundaries = [_outer(left, x0, "outer_left"),
                  _outer(right, x1, "outer_right")]
    internal = sorted(internal, key=lambda item: item[0])
    partial: list[float] = []
    for position, segments, coverage in internal:
        boundaries.append(VisualBoundary(
            x=position, role="internal", drawn=True,
            coverage=min(1.0, coverage),
            component_ids=sorted({s.component_id for s in segments}),
            segment_count=len(segments),
            segments=segments))
        if coverage < full:
            partial.append(position)
    boundaries.sort(key=lambda boundary: boundary.x)

    if not internal:
        status = "not_printed"
        columns = None
    elif partial:
        status = "partial"
        columns = len(internal) + 1
    elif not (boundaries[0].drawn and boundaries[-1].drawn):
        status = "implied_outer"
        columns = len(internal) + 1
    else:
        status = "printed"
        columns = len(internal) + 1

    return VisualStructure(
        boundaries=tuple(boundaries),
        visual_boundaries=tuple(boundary.x for boundary in boundaries),
        visual_boundary_status=status,
        visual_columns=columns,
        partial_boundaries=tuple(partial),
        region_height=height,
    )


__all__ = ["VisualStructure", "build_visual_structure"]
