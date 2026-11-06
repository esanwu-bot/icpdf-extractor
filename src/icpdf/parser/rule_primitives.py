"""Layer 1 - physical ruling primitives and their connected components.

A :class:`RulePrimitive` is one axis-aligned mark taken from the PDF vector
stream: a stroked/rectangular line (``line``), a thin rectangle
(``thin_rect``) or one axis-aligned edge of a stroked quadrilateral
(``quad_edge``).  Every primitive keeps the drawing element it came from so a
later table region can be traced back to the content stream.

Connected primitives form a :class:`RuleComponent`.  A component is a
*physical* object: a table frame, a figure box or a fragment of either.  It
makes no table claim - that decision belongs to region aggregation.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from icpdf.domain.common import BBox
from icpdf.parser.coords import PageGeometry

GRID_TOL = 2.5                # collinear / touching tolerance in PDF points
THIN_RECT_MAX_PT = 1.6       # a rectangle this thin is ruling, not a box
ORTHOGONAL_TOL_PT = 2.0      # endpoint skew still treated as axis-aligned
MAX_QUAD_STROKE_PT = 6.0     # thicker quads are frames/decoration, not ruling


@dataclass(frozen=True)
class RuleSegment:
    orientation: str          # "h" | "v"
    a: float                  # h: x0, v: y0
    b: float                  # h: x1, v: y1
    c: float                  # h: y,  v: x

    @property
    def length(self) -> float:
        return self.b - self.a


@dataclass(frozen=True)
class RulePrimitive:
    """One physical ruling mark, with its source drawing element."""

    page_number: int
    kind: str                 # "line" | "thin_rect" | "quad_edge"
    orientation: str          # "h" | "v"
    a: float
    b: float
    c: float
    weight: float = 0.0
    drawing_index: int = -1
    item_index: int = -1
    edge_index: int = 0

    @property
    def length(self) -> float:
        return self.b - self.a

    @property
    def segment(self) -> RuleSegment:
        return RuleSegment(self.orientation, self.a, self.b, self.c)


@dataclass(frozen=True)
class RuleComponent:
    """One connected lattice of ruling primitives.

    ``horizontal`` and ``vertical`` are collinear-merged spans used by the
    structure layer; ``primitives`` keeps every source mark that produced
    them, so the component stays auditable.
    """

    bbox: BBox
    horizontal: tuple[RuleSegment, ...]
    vertical: tuple[RuleSegment, ...]
    primitives: tuple[RulePrimitive, ...] = ()
    primitive_indices: tuple[int, ...] = ()
    page_number: int = 0
    component_id: int = 0


def _mark(p1, p2, *, page_number: int, kind: str, weight: float,
          drawing_index: int, item_index: int, edge_index: int,
          geometry: PageGeometry | None) -> RulePrimitive | None:
    dx, dy = abs(p1[0] - p2[0]), abs(p1[1] - p2[1])
    if dy <= ORTHOGONAL_TOL_PT and dx <= ORTHOGONAL_TOL_PT:
        return None
    if dy <= ORTHOGONAL_TOL_PT:
        orientation = "h"
    elif dx <= ORTHOGONAL_TOL_PT:
        orientation = "v"
    else:
        return None
    box = (min(p1[0], p2[0]), min(p1[1], p2[1]),
           max(p1[0], p2[0]), max(p1[1], p2[1]))
    if geometry is not None:
        box = geometry.to_display_bbox(box)
    if orientation == "h":
        return RulePrimitive(page_number, kind, "h", box[0], box[2],
                             (box[1] + box[3]) / 2.0, weight,
                             drawing_index, item_index, edge_index)
    return RulePrimitive(page_number, kind, "v", box[1], box[3],
                         (box[0] + box[2]) / 2.0, weight,
                         drawing_index, item_index, edge_index)


def _rect_mark(rect, *, page_number: int, weight: float,
               drawing_index: int, item_index: int,
               geometry: PageGeometry | None) -> RulePrimitive | None:
    if rect.height <= THIN_RECT_MAX_PT and rect.width > ORTHOGONAL_TOL_PT:
        orientation = "h"
    elif rect.width <= THIN_RECT_MAX_PT and rect.height > ORTHOGONAL_TOL_PT:
        orientation = "v"
    else:
        return None
    box = (rect.x0, rect.y0, rect.x1, rect.y1)
    if geometry is not None:
        box = geometry.to_display_bbox(box)
    if orientation == "h":
        return RulePrimitive(page_number, "thin_rect", "h", box[0], box[2],
                             (box[1] + box[3]) / 2.0, weight,
                             drawing_index, item_index, 0)
    return RulePrimitive(page_number, "thin_rect", "v", box[1], box[3],
                         (box[0] + box[2]) / 2.0, weight,
                         drawing_index, item_index, 0)


def collect_primitives(page, page_number: int,
                       geometry: PageGeometry | None = None, *,
                       include_quads: bool = True) -> list[RulePrimitive]:
    """All axis-aligned ruling marks on ``page``, in content-stream order.

    Quadrilateral cell outlines are a real ruling style (DS10CP152 p13).  A
    ``qu`` item contributes four edge primitives only when the drawing is
    stroked and thin; fill-only or thick quads are decoration and are skipped.
    """
    primitives: list[RulePrimitive] = []
    for drawing_index, drawing in enumerate(page.get_drawings()):
        drawing_type = drawing.get("type") or ""
        weight = float(drawing.get("width") or 0.0)
        for item_index, item in enumerate(drawing["items"]):
            kind = item[0]
            if kind == "l":
                primitive = _mark(item[1], item[2], page_number=page_number,
                                  kind="line", weight=weight,
                                  drawing_index=drawing_index,
                                  item_index=item_index, edge_index=0,
                                  geometry=geometry)
                if primitive is not None:
                    primitives.append(primitive)
            elif kind == "re":
                primitive = _rect_mark(item[1], page_number=page_number,
                                       weight=weight,
                                       drawing_index=drawing_index,
                                       item_index=item_index, geometry=geometry)
                if primitive is not None:
                    primitives.append(primitive)
            elif kind == "qu" and include_quads:
                if "s" not in drawing_type or weight > MAX_QUAD_STROKE_PT:
                    continue
                quad = item[1]
                for edge_index, (p1, p2) in enumerate((
                        (quad.ul, quad.ur), (quad.ll, quad.lr),
                        (quad.ul, quad.ll), (quad.ur, quad.lr))):
                    primitive = _mark(p1, p2, page_number=page_number,
                                      kind="quad_edge", weight=weight,
                                      drawing_index=drawing_index,
                                      item_index=item_index,
                                      edge_index=edge_index,
                                      geometry=geometry)
                    if primitive is not None:
                        primitives.append(primitive)
    return primitives


def merge_primitives(
    primitives: list[RulePrimitive], tol: float = GRID_TOL,
) -> list[tuple[RuleSegment, tuple[int, ...]]]:
    """Collinear-merge primitives, keeping the source indices per span."""
    merged: list[tuple[RuleSegment, tuple[int, ...]]] = []
    for orientation in ("h", "v"):
        items = sorted(((primitive, index)
                        for index, primitive in enumerate(primitives)
                        if primitive.orientation == orientation),
                       key=lambda entry: (entry[0].c, entry[0].a, entry[0].b))
        clusters: list[list[tuple[RulePrimitive, int]]] = []
        for primitive, index in items:
            if clusters and abs(primitive.c - median(
                    entry.c for entry, _ in clusters[-1])) <= tol:
                clusters[-1].append((primitive, index))
            else:
                clusters.append([(primitive, index)])
        for cluster in clusters:
            c = sum(entry.c for entry, _ in cluster) / len(cluster)
            spans = sorted((entry.a, entry.b, index) for entry, index in cluster)
            start, end, indices = spans[0][0], spans[0][1], [spans[0][2]]
            for a, b, index in spans[1:]:
                if a <= end + tol:
                    end = max(end, b)
                    indices.append(index)
                else:
                    merged.append((RuleSegment(orientation, start, end, c),
                                   tuple(sorted(indices))))
                    start, end, indices = a, b, [index]
            merged.append((RuleSegment(orientation, start, end, c),
                           tuple(sorted(indices))))
    return merged


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        ra, rb = self.find(left), self.find(right)
        if ra != rb:
            self.parent[rb] = ra


def build_components(primitives: list[RulePrimitive], *,
                     page_number: int = 1, tol: float = GRID_TOL,
                     min_width: float = 70.0,
                     min_height: float = 15.0) -> list[RuleComponent]:
    """Connected components of ruling; each dense component may be a table."""
    merged = merge_primitives(primitives, tol)
    horizontal = [(segment, indices) for segment, indices in merged
                  if segment.orientation == "h"]
    vertical = [(segment, indices) for segment, indices in merged
                if segment.orientation == "v"]
    spans = horizontal + vertical
    if not spans:
        return []
    uf = _UnionFind(len(spans))
    for i, (h, _) in enumerate(horizontal):
        for j, (v, _) in enumerate(vertical):
            if h.a - tol <= v.c <= h.b + tol and v.a - tol <= h.c <= v.b + tol:
                uf.union(i, len(horizontal) + j)
    groups: dict[int, list[int]] = {}
    for index in range(len(spans)):
        groups.setdefault(uf.find(index), []).append(index)

    components: list[RuleComponent] = []
    for ids in groups.values():
        hs = [spans[i] for i in ids if spans[i][0].orientation == "h"]
        vs = [spans[i] for i in ids if spans[i][0].orientation == "v"]
        if len(hs) < 2 or len(vs) < 2:
            continue
        xs = [segment.c for segment, _ in vs]
        ys = [segment.c for segment, _ in hs]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        if bbox[2] - bbox[0] < min_width or bbox[3] - bbox[1] < min_height:
            continue
        primitive_indices = sorted({index for _, indices in hs + vs
                                    for index in indices})
        components.append(RuleComponent(
            bbox=bbox,
            horizontal=tuple(segment for segment, _ in hs),
            vertical=tuple(segment for segment, _ in vs),
            primitives=tuple(primitives[i] for i in primitive_indices),
            primitive_indices=tuple(primitive_indices),
            page_number=page_number,
        ))
    components.sort(key=lambda component: (round(component.bbox[1], 1),
                                           round(component.bbox[0], 1)))
    return [RuleComponent(component.bbox, component.horizontal,
                          component.vertical, component.primitives,
                          component.primitive_indices, component.page_number,
                          component_id)
            for component_id, component in enumerate(components)]


__all__ = ["GRID_TOL", "RuleComponent", "RulePrimitive", "RuleSegment",
           "build_components", "collect_primitives", "merge_primitives"]
