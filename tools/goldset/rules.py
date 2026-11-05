"""Rule-lattice annotation primitives.

This module is *annotation tooling*, not the production detector.  It uses the
PDF's own vector ruling to propose a table grid so a human can review cells,
merged spans and column roles.  It intentionally does not reuse
``icpdf.parser.table_detector``: the gold set must not be produced by the thing
it is meant to evaluate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median

import pymupdf

TOL = 2.5
MIN_COMPONENT_WIDTH = 70.0
MIN_COMPONENT_HEIGHT = 15.0


@dataclass(frozen=True)
class Segment:
    orientation: str          # "h" | "v"
    a: float                  # h: x0, v: y0
    b: float                  # h: x1, v: y1
    c: float                  # h: y,  v: x

    @property
    def length(self) -> float:
        return self.b - self.a


@dataclass(frozen=True)
class RuleComponent:
    bbox: tuple[float, float, float, float]
    horizontal: tuple[Segment, ...]
    vertical: tuple[Segment, ...]


@dataclass
class GridCell:
    row: int
    column: int
    row_span: int
    column_span: int
    bbox: tuple[float, float, float, float]
    text: str = ""
    word_count: int = 0


@dataclass
class RuleGrid:
    bbox: tuple[float, float, float, float]
    xs: list[float]
    ys: list[float]
    cells: list[GridCell] = field(default_factory=list)
    unassigned_words: list[tuple[float, float, float, float, str]] = field(default_factory=list)


def _as_segment(p1, p2) -> Segment | None:
    if abs(p1[1] - p2[1]) < abs(p1[0] - p2[0]):
        if abs(p1[0] - p2[0]) < 2.0:
            return None
        return Segment("h", min(p1[0], p2[0]), max(p1[0], p2[0]), (p1[1] + p2[1]) / 2.0)
    if abs(p1[1] - p2[1]) < 2.0:
        return None
    return Segment("v", min(p1[1], p2[1]), max(p1[1], p2[1]), (p1[0] + p2[0]) / 2.0)


def page_segments(page: pymupdf.Page) -> list[Segment]:
    """Collect thin horizontal/vertical ruling, including thin filled rects."""
    raw: list[Segment] = []
    for drawing in page.get_drawings():
        for item in drawing["items"]:
            kind = item[0]
            if kind == "l":
                seg = _as_segment(item[1], item[2])
                if seg:
                    raw.append(seg)
            elif kind == "re":
                rect = item[1]
                if rect.height <= 1.6 and rect.width > 2.0:
                    raw.append(Segment("h", rect.x0, rect.x1, (rect.y0 + rect.y1) / 2.0))
                elif rect.width <= 1.6 and rect.height > 2.0:
                    raw.append(Segment("v", rect.y0, rect.y1, (rect.x0 + rect.x1) / 2.0))
    return _merge_collinear(raw)


def _merge_collinear(segments: list[Segment], tol: float = TOL) -> list[Segment]:
    merged: list[Segment] = []
    for orientation in ("h", "v"):
        items = sorted((s for s in segments if s.orientation == orientation),
                       key=lambda s: (s.c, s.a, s.b))
        clusters: list[list[Segment]] = []
        for seg in items:
            if clusters and abs(seg.c - median([x.c for x in clusters[-1]])) <= tol:
                clusters[-1].append(seg)
            else:
                clusters.append([seg])
        for cluster in clusters:
            c = sum(x.c for x in cluster) / len(cluster)
            spans = sorted((x.a, x.b) for x in cluster)
            start, end = spans[0]
            for a, b in spans[1:]:
                if a <= end + tol:
                    end = max(end, b)
                else:
                    merged.append(Segment(orientation, start, end, c))
                    start, end = a, b
            merged.append(Segment(orientation, start, end, c))
    return merged


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def rule_components(page: pymupdf.Page, tol: float = TOL) -> list[RuleComponent]:
    """Connected components of ruling.  Each dense component is a ruled table."""
    segments = page_segments(page)
    horizontal = [s for s in segments if s.orientation == "h"]
    vertical = [s for s in segments if s.orientation == "v"]
    all_segments = horizontal + vertical
    if not all_segments:
        return []
    uf = _UnionFind(len(all_segments))
    h_buckets: dict[int, list[int]] = {}
    for i, seg in enumerate(horizontal):
        for bucket in range(int((seg.a - tol) // 12), int((seg.b + tol) // 12) + 1):
            h_buckets.setdefault(bucket, []).append(i)
    v_buckets: dict[int, list[int]] = {}
    for j, seg in enumerate(vertical):
        for bucket in range(int((seg.a - tol) // 12), int((seg.b + tol) // 12) + 1):
            v_buckets.setdefault(bucket, []).append(len(horizontal) + j)
    for i, h in enumerate(horizontal):
        for j, v in enumerate(vertical):
            if h.a - tol <= v.c <= h.b + tol and v.a - tol <= h.c <= v.b + tol:
                uf.union(i, len(horizontal) + j)
    groups: dict[int, list[int]] = {}
    for i in range(len(all_segments)):
        groups.setdefault(uf.find(i), []).append(i)
    out: list[RuleComponent] = []
    for ids in groups.values():
        hs = [all_segments[i] for i in ids if all_segments[i].orientation == "h"]
        vs = [all_segments[i] for i in ids if all_segments[i].orientation == "v"]
        if len(hs) < 2 or len(vs) < 2:
            continue
        xs = [s.c for s in vs]
        ys = [s.c for s in hs]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        if bbox[2] - bbox[0] < MIN_COMPONENT_WIDTH:
            continue
        if bbox[3] - bbox[1] < MIN_COMPONENT_HEIGHT:
            continue
        out.append(RuleComponent(bbox, tuple(hs), tuple(vs)))
    out.sort(key=lambda c: (round(c.bbox[1], 1), round(c.bbox[0], 1)))
    return out


def _unique(values: list[float], tol: float = TOL) -> list[float]:
    out: list[float] = []
    for value in sorted(values):
        if not out or value - out[-1] > tol:
            out.append(value)
        else:
            out[-1] = (out[-1] + value) / 2.0
    return out


def _coverage(segments: tuple[Segment, ...], position: float,
              start: float, end: float, tol: float = TOL) -> float:
    if end <= start:
        return 1.0
    spans = sorted((max(start, s.a), min(end, s.b)) for s in segments
                   if abs(s.c - position) <= tol and s.a < end and s.b > start)
    if not spans:
        return 0.0
    covered = 0.0
    cur_a, cur_b = spans[0]
    for a, b in spans[1:]:
        if a <= cur_b + tol:
            cur_b = max(cur_b, b)
        else:
            covered += max(0.0, cur_b - cur_a)
            cur_a, cur_b = a, b
    covered += max(0.0, cur_b - cur_a)
    return covered / (end - start)


def _word_runs_in_band(page: pymupdf.Page, y0: float, y1: float,
                       gap: float = 8.0) -> list[tuple[float, float]]:
    """Connected word runs for one row band.

    A visual body row contains several separate runs (one per cell); a spanning
    cell contains one run whose bbox crosses an implicit column boundary.
    """
    words = [w for w in page.get_text("words", sort=False)
             if y0 - 1.0 <= (w[1] + w[3]) / 2.0 <= y1 + 1.0]
    words.sort(key=lambda w: (w[0], (w[1] + w[3]) / 2.0))
    runs: list[list[tuple]] = []
    for word in words:
        if runs and word[0] - max(w[2] for w in runs[-1]) <= gap:
            runs[-1].append(word)
        else:
            runs.append([word])
    return [(min(w[0] for w in run), max(w[2] for w in run)) for run in runs]


def _projection_column_boundaries(page: pymupdf.Page,
                                  bbox: tuple[float, float, float, float],
                                  gap: float = 7.0) -> list[float]:
    """Whitespace gutters across all rows: fallback for vertical-rule-free tables."""
    intervals = sorted((w[0], w[2]) for w in page.get_text("words", sort=False)
                       if bbox[0] - 1.0 <= (w[0] + w[2]) / 2.0 <= bbox[2] + 1.0
                       and bbox[1] - 1.0 <= (w[1] + w[3]) / 2.0 <= bbox[3] + 1.0)
    if len(intervals) < 2:
        return [bbox[0], bbox[2]]
    runs: list[list[float]] = []
    for a, b in intervals:
        if runs and a - runs[-1][1] <= 1.5:
            runs[-1][1] = max(runs[-1][1], b)
        else:
            runs.append([a, b])
    xs = [bbox[0]]
    for i in range(len(runs) - 1):
        if runs[i + 1][0] - runs[i][1] >= gap:
            xs.append((runs[i][1] + runs[i + 1][0]) / 2.0)
    xs.append(bbox[2])
    return _unique(xs, 2.0)


def _header_column_boundaries(page: pymupdf.Page, y0: float, y1: float,
                              outer: tuple[float, float]) -> list[float]:
    """Fallback for tables whose body has no vertical rules."""
    return _projection_column_boundaries(page, (outer[0], y0, outer[1], y1))


def build_rule_grid(page: pymupdf.Page, component: RuleComponent,
                    header_rows: int = 0, column_boundaries: list[float] | None = None,
                    full_width_rows: set[int] | None = None,
                    merges: list[tuple[int, int, int, int]] | None = None,
                    no_merge: set[tuple[int, int]] | None = None,
                    row_boundaries: list[float] | None = None,
                    bbox: tuple[float, float, float, float] | None = None,
                    tol: float = TOL) -> RuleGrid:
    all_xs = _unique([s.c for s in component.vertical if 4.0 <= s.length], tol)
    internal_xs = [x for x in all_xs
                   if component.bbox[0] + 3.0 < x < component.bbox[2] - 3.0]
    if row_boundaries:
        ys = _unique(list(row_boundaries), tol)
    else:
        ys = _unique([component.bbox[1], component.bbox[3]]
                     + [s.c for s in component.horizontal if 2.0 <= s.length], tol)
    if column_boundaries:
        xs = _unique(list(column_boundaries), tol)
        use_rule_columns = False
    elif internal_xs:
        xs = _unique([component.bbox[0], component.bbox[2]] + internal_xs, tol)
        use_rule_columns = True
    else:
        xs = _projection_column_boundaries(page, component.bbox)
        use_rule_columns = False
    if len(xs) < 2 or len(ys) < 2:
        return RuleGrid(component.bbox, xs, ys)

    grid_bbox = bbox or component.bbox
    nr, nc = len(ys) - 1, len(xs) - 1
    uf = _UnionFind(nr * nc)
    body_runs: dict[int, list[tuple[float, float]]] = {}
    for i in range(nr):
        if i >= header_rows:
            body_runs[i] = _word_runs_in_band(page, ys[i], ys[i + 1])
        for j in range(nc):
            idx = i * nc + j
            if j + 1 < nc:
                boundary = xs[j + 1]
                if no_merge and (i, j) in no_merge:
                    crossed = False
                elif full_width_rows and i in full_width_rows:
                    crossed = True
                elif i < header_rows and use_rule_columns:
                    crossed = _coverage(component.vertical, boundary,
                                        ys[i], ys[i + 1], tol) < 0.55
                elif i < header_rows:
                    # Explicit boundaries already state the logical columns; do
                    # not re-infer header canopies from word proximity.
                    crossed = False
                else:
                    if not body_runs.get(i):
                        body_runs[i] = _word_runs_in_band(page, ys[i], ys[i + 1])
                    crossed = any(a <= boundary - 2.0 and b >= boundary + 2.0
                                  for a, b in body_runs.get(i, []))
                if crossed:
                    uf.union(idx, idx + 1)
            if i + 1 < nr:
                boundary = ys[i + 1]
                if _coverage(component.horizontal, boundary, xs[j], xs[j + 1], tol) < 0.55:
                    uf.union(idx, idx + nc)

    # Explicit canopy merges (e.g. a header spanning several sub-columns) that
    # rule coverage alone cannot infer.
    for row_start, row_end, col_start, col_end in merges or []:
        anchor = row_start * nc + col_start
        for row in range(row_start, row_end + 1):
            for col in range(col_start, col_end + 1):
                uf.union(anchor, row * nc + col)

    groups: dict[int, list[tuple[int, int]]] = {}
    for i in range(nr):
        for j in range(nc):
            groups.setdefault(uf.find(i * nc + j), []).append((i, j))

    cells: list[GridCell] = []
    for members in groups.values():
        rows = [p[0] for p in members]
        cols = [p[1] for p in members]
        r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
        cells.append(GridCell(r0, c0, r1 - r0 + 1, c1 - c0 + 1,
                              (xs[c0], ys[r0], xs[c1 + 1], ys[r1 + 1])))
    cells.sort(key=lambda c: (c.row, c.column))

    grid = RuleGrid(grid_bbox, xs, ys, cells)
    _assign_words(page, grid)
    return grid


def _assign_words(page: pymupdf.Page, grid: RuleGrid) -> None:
    words = []
    seen: set[tuple[float, float, float, float, str]] = set()
    for word in page.get_text("words", sort=False):
        # Some datasheets overprint the same text object twice; keep one copy
        # so a printed label such as UNIT is not concatenated as UNIT UNIT.
        key = (round(word[0], 2), round(word[1], 2), round(word[2], 2),
               round(word[3], 2), word[4])
        if key in seen:
            continue
        seen.add(key)
        words.append(word)
    by_cell: dict[int, list[tuple[float, float, float, float, str]]] = {}
    for word in words:
        x0, y0, x1, y1, text = word[:5]
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        target = None
        for index, cell in enumerate(grid.cells):
            bx0, by0, bx1, by1 = cell.bbox
            if bx0 - 0.8 <= cx <= bx1 + 0.8 and by0 - 0.8 <= cy <= by1 + 0.8:
                target = index
                break
        if target is None:
            if (grid.bbox[0] <= cx <= grid.bbox[2]
                    and grid.bbox[1] <= cy <= grid.bbox[3]):
                grid.unassigned_words.append((x0, y0, x1, y1, text))
            continue
        by_cell.setdefault(target, []).append((x0, y0, x1, y1, text))
    for index, items in by_cell.items():
        grid.cells[index].text = _words_to_text(items)
        grid.cells[index].word_count = len(items)


def _words_to_text(items: list[tuple[float, float, float, float, str]]) -> str:
    items = sorted(items, key=lambda w: ((w[1] + w[3]) / 2.0, w[0]))
    heights = [w[3] - w[1] for w in items if w[3] > w[1]]
    line_tol = max(2.0, (median(heights) if heights else 8.0) * 0.55)
    lines: list[list[tuple[float, float, float, float, str]]] = []
    centers: list[float] = []
    for item in items:
        center = (item[1] + item[3]) / 2.0
        if lines and abs(center - centers[-1]) <= line_tol:
            lines[-1].append(item)
            centers[-1] = sum((w[1] + w[3]) / 2.0 for w in lines[-1]) / len(lines[-1])
        else:
            lines.append([item])
            centers.append(center)
    rendered: list[str] = []
    for line in lines:
        line = sorted(line, key=lambda w: w[0])
        rendered.append(" ".join(w[4] for w in line))
    return "\n".join(rendered).strip()
