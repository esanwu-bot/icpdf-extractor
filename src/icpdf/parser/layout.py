"""Layer 1 - page layout analysis.

Collects the three deterministic inputs later layers operate on: text words,
baseline row bands, and connected components of thin vector ruling.  This module
makes no table decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from icpdf.domain.common import BBox
from icpdf.parser.coords import PageGeometry
from icpdf.parser.text_blocks import TextBlock, TextWord

GRID_TOL = 2.5


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
class RuleComponent:
    """One connected lattice of horizontal and vertical ruling."""

    bbox: BBox
    horizontal: tuple[RuleSegment, ...]
    vertical: tuple[RuleSegment, ...]


@dataclass(frozen=True)
class PageLayout:
    page_number: int
    rect: BBox
    blocks: list[TextBlock]
    words: list[TextWord]
    row_bands: list[list[TextWord]]
    components: list[RuleComponent]


def _display_segment(p1, p2, geometry: PageGeometry | None) -> RuleSegment | None:
    dx, dy = abs(p1[0] - p2[0]), abs(p1[1] - p2[1])
    if dy <= 2.0 and dx <= 2.0:
        return None
    if dy <= 2.0:
        orientation = "h"
    elif dx <= 2.0:
        orientation = "v"
    else:
        return None
    box = (min(p1[0], p2[0]), min(p1[1], p2[1]),
           max(p1[0], p2[0]), max(p1[1], p2[1]))
    if geometry is not None:
        box = geometry.to_display_bbox(box)
    if orientation == "h":
        return RuleSegment("h", box[0], box[2], (box[1] + box[3]) / 2.0)
    return RuleSegment("v", box[1], box[3], (box[0] + box[2]) / 2.0)


def page_segments(page, geometry: PageGeometry | None = None) -> list[RuleSegment]:
    """Thin horizontal/vertical ruling, including thin filled rectangles."""
    raw: list[RuleSegment] = []
    for drawing in page.get_drawings():
        for item in drawing["items"]:
            if item[0] == "l":
                segment = _display_segment(item[1], item[2], geometry)
                if segment is not None:
                    raw.append(segment)
            elif item[0] == "re":
                rect = item[1]
                if rect.height <= 1.6 and rect.width > 2.0:
                    orientation = "h"
                elif rect.width <= 1.6 and rect.height > 2.0:
                    orientation = "v"
                else:
                    continue
                box = (rect.x0, rect.y0, rect.x1, rect.y1)
                if geometry is not None:
                    box = geometry.to_display_bbox(box)
                if orientation == "h":
                    raw.append(RuleSegment("h", box[0], box[2], (box[1] + box[3]) / 2.0))
                else:
                    raw.append(RuleSegment("v", box[1], box[3], (box[0] + box[2]) / 2.0))
    return _merge_collinear(raw)


def _merge_collinear(segments: list[RuleSegment], tol: float = GRID_TOL) -> list[RuleSegment]:
    merged: list[RuleSegment] = []
    for orientation in ("h", "v"):
        items = sorted((s for s in segments if s.orientation == orientation),
                       key=lambda s: (s.c, s.a, s.b))
        clusters: list[list[RuleSegment]] = []
        for segment in items:
            if clusters and abs(segment.c - median(x.c for x in clusters[-1])) <= tol:
                clusters[-1].append(segment)
            else:
                clusters.append([segment])
        for cluster in clusters:
            c = sum(x.c for x in cluster) / len(cluster)
            spans = sorted((x.a, x.b) for x in cluster)
            start, end = spans[0]
            for a, b in spans[1:]:
                if a <= end + tol:
                    end = max(end, b)
                else:
                    merged.append(RuleSegment(orientation, start, end, c))
                    start, end = a, b
            merged.append(RuleSegment(orientation, start, end, c))
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


def rule_components(page, geometry: PageGeometry | None = None,
                    *, tol: float = GRID_TOL,
                    min_width: float = 70.0,
                    min_height: float = 15.0) -> list[RuleComponent]:
    """Connected components of ruling; each dense component may be a table."""
    segments = page_segments(page, geometry)
    horizontal = [s for s in segments if s.orientation == "h"]
    vertical = [s for s in segments if s.orientation == "v"]
    all_segments = horizontal + vertical
    if not all_segments:
        return []
    uf = _UnionFind(len(all_segments))
    for i, h in enumerate(horizontal):
        for j, v in enumerate(vertical):
            if h.a - tol <= v.c <= h.b + tol and v.a - tol <= h.c <= v.b + tol:
                uf.union(i, len(horizontal) + j)
    groups: dict[int, list[int]] = {}
    for index in range(len(all_segments)):
        groups.setdefault(uf.find(index), []).append(index)
    components: list[RuleComponent] = []
    for ids in groups.values():
        hs = [all_segments[i] for i in ids if all_segments[i].orientation == "h"]
        vs = [all_segments[i] for i in ids if all_segments[i].orientation == "v"]
        if len(hs) < 2 or len(vs) < 2:
            continue
        xs = [s.c for s in vs]
        ys = [s.c for s in hs]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        if bbox[2] - bbox[0] < min_width or bbox[3] - bbox[1] < min_height:
            continue
        components.append(RuleComponent(bbox, tuple(hs), tuple(vs)))
    components.sort(key=lambda c: (round(c.bbox[1], 1), round(c.bbox[0], 1)))
    return components


def _row_bands(words: list[TextWord]) -> list[list[TextWord]]:
    if not words:
        return []
    heights = [w.bbox[3] - w.bbox[1] for w in words if w.bbox[3] > w.bbox[1]]
    tolerance = max(3.0, (median(heights) if heights else 10.0) * 0.5)
    ordered = sorted(words, key=lambda w: ((w.bbox[1] + w.bbox[3]) / 2.0, w.bbox[0]))
    bands: list[list[TextWord]] = []
    centers: list[float] = []
    for word in ordered:
        center = (word.bbox[1] + word.bbox[3]) / 2.0
        if bands and abs(center - centers[-1]) <= tolerance:
            bands[-1].append(word)
            centers[-1] = sum((w.bbox[1] + w.bbox[3]) / 2.0 for w in bands[-1]) / len(bands[-1])
        else:
            bands.append([word])
            centers.append(center)
    return [sorted(band, key=lambda w: w.bbox[0]) for band in bands]


def analyze_layout(page, blocks: list[TextBlock], page_number: int, *,
                   geometry: PageGeometry | None = None,
                   min_rule_width: float = 70.0,
                   min_rule_height: float = 15.0) -> PageLayout:
    words = [word for block in blocks for line in block.lines for word in line.words]
    components = (rule_components(page, geometry, min_width=min_rule_width,
                                  min_height=min_rule_height)
                  if page is not None else [])
    return PageLayout(
        page_number=page_number,
        rect=(page.rect.x0, page.rect.y0, page.rect.x1, page.rect.y1) if page is not None
        else (0.0, 0.0, 612.0, 792.0),
        blocks=blocks,
        words=words,
        row_bands=_row_bands(words),
        components=components,
    )


__all__ = ["PageLayout", "RuleComponent", "RuleSegment", "analyze_layout",
           "page_segments", "rule_components"]
