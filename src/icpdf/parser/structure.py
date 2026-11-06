"""Layer 3 - table structure recognition.

Turns a table region plus the page layout into a row/column grid.  Two evidence
paths are supported:

* ``rule_lattice`` - the region has vector ruling; rules give hard boundaries,
  text gutters add soft boundaries for logically split columns, and cells are
  merged only where a rule is missing *and* text runs across the boundary.
* ``text_alignment`` - no ruling; stable baseline rows and column starts give a
  grid.  This path requires at least :attr:`TableParams.alignment_min_rows`
  visual rows, so it never invents a table from a single prose line.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median

from icpdf.domain.common import BBox
from icpdf.parser.config import TableParams
from icpdf.parser.layout import PageLayout, RuleComponent, RuleSegment
from icpdf.parser.text_blocks import TextWord

TOL = 2.5


@dataclass(frozen=True)
class RegionEvidence:
    """One auditable step behind a :class:`TableRegion`.

    ``kind`` is ``merge`` (two stacked components share a column lattice),
    ``absorbed`` (a member is carried by the region instead of emitted on its
    own) or ``implied_outer`` (a left/right boundary comes from the common
    horizontal-rule extent rather than a vertical rule).
    """

    kind: str
    detail: str
    component_ids: tuple[int, ...] = ()
    values: tuple[float, ...] = ()


@dataclass(frozen=True)
class TableRegion:
    page_number: int
    bbox: BBox
    source: str                       # "rule_lattice" | "text_alignment"
    component: RuleComponent | None = None
    rows_words: tuple[tuple[TextWord, ...], ...] = ()
    components: tuple[RuleComponent, ...] = ()
    boundary_source: str = "ruled"    # ruled | implied_horizontal |
                                      # implied_alignment | mixed
    evidence: tuple[RegionEvidence, ...] = ()


@dataclass
class GridCell:
    row: int
    column: int
    row_span: int
    column_span: int
    bbox: BBox
    text: str = ""
    word_count: int = 0


@dataclass
class TableGrid:
    bbox: BBox
    xs: list[float]
    ys: list[float]
    cells: list[GridCell] = field(default_factory=list)
    unassigned_words: list[TextWord] = field(default_factory=list)
    source: str = "rule_lattice"

    @property
    def n_rows(self) -> int:
        return len(self.ys) - 1

    @property
    def n_columns(self) -> int:
        return len(self.xs) - 1


def _unique(values: list[float], tol: float = TOL) -> list[float]:
    out: list[float] = []
    for value in sorted(values):
        if not out or value - out[-1] > tol:
            out.append(value)
        else:
            out[-1] = (out[-1] + value) / 2.0
    return out


def _coverage(segments: tuple[RuleSegment, ...], position: float,
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


def _word_runs(layout: PageLayout, y0: float, y1: float,
               gap: float = 8.0) -> list[tuple[float, float]]:
    words = [w for w in layout.words
             if y0 - 1.0 <= (w.bbox[1] + w.bbox[3]) / 2.0 <= y1 + 1.0]
    words.sort(key=lambda w: (w.bbox[0], (w.bbox[1] + w.bbox[3]) / 2.0))
    runs: list[list[TextWord]] = []
    for word in words:
        if runs and word.bbox[0] - max(w.bbox[2] for w in runs[-1]) <= gap:
            runs[-1].append(word)
        else:
            runs.append([word])
    return [(min(w.bbox[0] for w in run), max(w.bbox[2] for w in run)) for run in runs]


def _band_gaps(layout: PageLayout, ys: list[float],
               gap: float) -> list[list[tuple[float, float, float]]]:
    """Per-band gutters as ``(left_run_end, right_run_start, midpoint)``."""
    bands: list[list[tuple[float, float, float]]] = []
    for y0, y1 in zip(ys, ys[1:]):
        words = [w for w in layout.words
                 if y0 - 1.0 <= (w.bbox[1] + w.bbox[3]) / 2.0 <= y1 + 1.0]
        if len(words) < 2:
            continue
        words.sort(key=lambda w: w.bbox[0])
        runs: list[list[float]] = []
        for word in words:
            if runs and word.bbox[0] - runs[-1][1] <= gap:
                runs[-1][1] = max(runs[-1][1], word.bbox[2])
            else:
                runs.append([word.bbox[0], word.bbox[2]])
        if len(runs) < 2:
            continue
        bands.append([(runs[i][1], runs[i + 1][0], (runs[i][1] + runs[i + 1][0]) / 2.0)
                      for i in range(len(runs) - 1)
                      if runs[i + 1][0] - runs[i][1] >= gap])
    return bands


def _projection_boundaries(layout: PageLayout, bbox: BBox, ys: list[float],
                           gap: float = 7.0, min_support: float = 0.4
                           ) -> list[tuple[float, float, float]]:
    """Recurring column gutters, as ``(left_end, right_start, midpoint)``.

    Pooling word intervals across the whole table would invent boundaries from
    per-row whitespace (prose conditions, multi-line cells).  A boundary is kept
    only when a gutter exists at the same x in a large fraction of row bands.
    """
    bands = _band_gaps(layout, ys, gap)
    if not bands:
        return []
    clusters: list[dict] = []
    for band_index, gaps in enumerate(bands):
        for left, right, mid in gaps:
            for cluster in clusters:
                if abs(mid - cluster["pos"]) <= 5.0:
                    cluster["values"].append(mid)
                    cluster["bands"].add(band_index)
                    cluster["left"] = min(cluster["left"], left)
                    cluster["right"] = max(cluster["right"], right)
                    cluster["pos"] = sum(cluster["values"]) / len(cluster["values"])
                    break
            else:
                clusters.append({"pos": mid, "values": [mid], "bands": {band_index},
                                 "left": left, "right": right})
    need = max(2, int(len(bands) * min_support))
    return sorted((cluster["left"], cluster["right"], cluster["pos"])
                  for cluster in clusters
                  if len(cluster["bands"]) >= need
                  and bbox[0] + 3.0 < cluster["pos"] < bbox[2] - 3.0)


def _header_boundaries(layout: PageLayout, bbox: BBox, ys: list[float],
                       bands: int = 2, gap: float = 9.0
                       ) -> list[tuple[float, float, float]]:
    """Candidate boundaries from header word runs (MIN/TYP/MAX-like columns).

    Returns ``(left_end, right_start, midpoint)`` so callers can tell whether a
    hard rule already occupies the same header gap.
    """
    boundaries: list[tuple[float, float, float]] = []
    for band in range(min(bands, max(0, len(ys) - 1))):
        runs = _word_runs(layout, ys[band], ys[band + 1], gap=gap)
        if band > 0:
            # Only a label row may extend the header.  A body row with a long
            # wrapped phrase (section title, group name) is not a header row.
            long_runs = [run for run in runs if run[1] - run[0] > 50.0]
            if long_runs or len(runs) < 2:
                break
        for index in range(len(runs) - 1):
            left, right = runs[index][1], runs[index + 1][0]
            gap_width = right - left
            if gap_width < 4.0:
                continue
            # In a wide gap the centred label says little about the column edge;
            # the next label's left edge is the reliable column start.
            candidate = ((left + right) / 2.0 if gap_width <= 80.0
                         else right - 4.0)
            boundaries.append((left, right, candidate))
    deduped: list[tuple[float, float, float]] = []
    for entry in boundaries:
        if any(abs(entry[2] - kept[2]) <= 12.0 for kept in deduped):
            continue
        if bbox[0] + 3.0 < entry[2] < bbox[2] - 3.0:
            deduped.append(entry)
    return deduped


def _band_runs(layout: PageLayout, ys: list[float],
               gap: float) -> list[list[list[float]]]:
    bands: list[list[list[float]]] = []
    for y0, y1 in zip(ys, ys[1:]):
        words = [w for w in layout.words
                 if y0 - 1.0 <= (w.bbox[1] + w.bbox[3]) / 2.0 <= y1 + 1.0]
        if not words:
            continue
        words.sort(key=lambda w: w.bbox[0])
        runs: list[list[float]] = []
        for word in words:
            if runs and word.bbox[0] - runs[-1][1] <= gap:
                runs[-1][1] = max(runs[-1][1], word.bbox[2])
            else:
                runs.append([word.bbox[0], word.bbox[2]])
        bands.append(runs)
    return bands


def _header_words_between(layout: PageLayout, ys: list[float],
                          lo: float, hi: float, bands: int = 1) -> bool:
    for band in range(min(bands, max(0, len(ys) - 1))):
        for word in layout.words:
            center_y = (word.bbox[1] + word.bbox[3]) / 2.0
            if ys[band] - 1.0 <= center_y <= ys[band + 1] + 1.0:
                center_x = (word.bbox[0] + word.bbox[2]) / 2.0
                if lo < center_x < hi:
                    return True
    return False


def _band_coverage(segments, x: float, ys: list[float],
                   layout: PageLayout | None = None, tol: float = TOL) -> float:
    """Fraction of row bands where a vertical rule spans the band.

    Summed rule length accepts nested sub-boxes (conditions, MIN/MAX boxes)
    that are drawn only on part of the table; a logical column rule runs
    through nearly every row band.  Bands where text crosses ``x`` are counted
    as support too: a merged cell is evidence the boundary is real but
    suppressed, not evidence against the column.
    """
    hits = total = 0
    for y0, y1 in zip(ys, ys[1:]):
        if y1 - y0 < 2.0:
            continue
        total += 1
        covered = sum(max(0.0, min(segment.b, y1) - max(segment.a, y0))
                      for segment in segments if abs(segment.c - x) <= tol)
        if covered >= (y1 - y0) * 0.6:
            hits += 1
        elif layout is not None and _text_crosses(layout, x, y0, y1):
            hits += 1
    return hits / total if total else 0.0


def _text_crosses(layout: PageLayout, x: float, y0: float, y1: float) -> bool:
    return any(word.bbox[0] < x - 2.0 and word.bbox[2] > x + 2.0
               for word in layout.words
               if y0 - 1.0 <= (word.bbox[1] + word.bbox[3]) / 2.0 <= y1 + 1.0)


def _crossing_ratio(bands: list[list[list[float]]], x: float) -> tuple[float, float]:
    """Fraction of bands with a word run crossing ``x`` vs a gutter at ``x``."""
    crossing = gutter = total = 0
    for runs in bands:
        total += 1
        if any(run[0] < x - 2.0 and run[1] > x + 2.0 for run in runs):
            crossing += 1
        elif any(run[1] <= x - 2.0 for run in runs) and any(
                run[0] >= x + 2.0 for run in runs):
            gutter += 1
    return (crossing / total if total else 0.0,
            gutter / total if total else 0.0)


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


def _assign_words(layout: PageLayout, grid: TableGrid) -> None:
    by_cell: dict[int, list[TextWord]] = {}
    for word in layout.words:
        cx = (word.bbox[0] + word.bbox[2]) / 2.0
        cy = (word.bbox[1] + word.bbox[3]) / 2.0
        target = None
        for index, cell in enumerate(grid.cells):
            x0, y0, x1, y1 = cell.bbox
            if x0 - 0.8 <= cx <= x1 + 0.8 and y0 - 0.8 <= cy <= y1 + 0.8:
                target = index
                break
        if target is None:
            if (grid.bbox[0] <= cx <= grid.bbox[2]
                    and grid.bbox[1] <= cy <= grid.bbox[3]):
                grid.unassigned_words.append(word)
            continue
        by_cell.setdefault(target, []).append(word)
    for index, words in by_cell.items():
        grid.cells[index].text = _words_to_text(words)
        grid.cells[index].word_count = len(words)


def _words_to_text(words: list[TextWord]) -> str:
    ordered = sorted(words, key=lambda w: ((w.bbox[1] + w.bbox[3]) / 2.0, w.bbox[0]))
    heights = [w.bbox[3] - w.bbox[1] for w in ordered if w.bbox[3] > w.bbox[1]]
    line_tol = max(2.0, (median(heights) if heights else 8.0) * 0.55)
    lines: list[list[TextWord]] = []
    centers: list[float] = []
    for word in ordered:
        center = (word.bbox[1] + word.bbox[3]) / 2.0
        if lines and abs(center - centers[-1]) <= line_tol:
            lines[-1].append(word)
            centers[-1] = sum((w.bbox[1] + w.bbox[3]) / 2.0 for w in lines[-1]) / len(lines[-1])
        else:
            lines.append([word])
            centers.append(center)
    rendered = [" ".join(w.text for w in sorted(line, key=lambda w: w.bbox[0]))
                for line in lines]
    return "\n".join(rendered).strip()


def _member_ys(member: RuleComponent) -> list[float]:
    return _unique([member.bbox[1], member.bbox[3]]
                   + [segment.c for segment in member.horizontal
                      if segment.length >= 2.0
                      and member.bbox[1] - TOL <= segment.c <= member.bbox[3] + TOL])


def _member_column_support(member: RuleComponent, x: float, layout: PageLayout,
                           params: TableParams) -> bool:
    """Whether one physical component backs ``x`` as a column boundary.

    A merged region is taller than any of its components, so whole-region
    coverage would reject every section-local rule.  Each component is judged
    against its own row bands instead.
    """
    ys = _member_ys(member)
    if len(ys) < 2:
        return False
    coverage = _band_coverage(member.vertical, x, ys, layout)
    if coverage < 0.7:
        return False
    if coverage >= 0.999:
        return True
    return _crossing_ratio(_band_runs(layout, ys, params.cell_gap_pt),
                           x)[0] < 0.4


def _rule_grid(layout: PageLayout, region: TableRegion, params: TableParams) -> TableGrid:
    component = region.component
    assert component is not None
    bbox = component.bbox
    hard_xs = _unique([s.c for s in component.vertical if s.length >= 4.0], 4.0)
    hard_xs = [x for x in hard_xs if bbox[0] - TOL <= x <= bbox[2] + TOL]
    ys = _unique([bbox[1], bbox[3]]
                 + [s.c for s in component.horizontal if s.length >= 2.0
                    and bbox[1] - TOL <= s.c <= bbox[3] + TOL])
    rule_ys = set(ys)

    if len(ys) < 3:
        # No internal horizontal rule: fall back to text-line centres.  When a
        # real rule exists, splitting every physical line would double the row
        # count of tables whose header wraps onto two lines.
        centers = sorted((w.bbox[1] + w.bbox[3]) / 2.0 for w in layout.words
                         if bbox[1] <= (w.bbox[1] + w.bbox[3]) / 2.0 <= bbox[3])
        centers = _unique(centers, 4.0)
        additions = [(a + b) / 2.0 for a, b in zip(centers, centers[1:])]
        ys = _unique(ys + additions, 3.0)

    body_runs = _band_runs(layout, ys, params.cell_gap_pt)
    members = region.components if len(region.components) > 1 else ()

    def _is_column_rule(x: float) -> bool:
        if members:
            return any(_member_column_support(member, x, layout, params)
                       for member in members)
        # Nested TEST CONDITIONS boxes have enough total length but run through
        # only part of the table; logical columns run through most row bands
        # (bands where text crosses the boundary count as merged-cell support).
        coverage = _band_coverage(component.vertical, x, ys, layout)
        if coverage < 0.7:
            return False
        # A rule drawn through every row band is structural; tight header words
        # (superscript notes) may touch it without making it a text gutter.
        return coverage >= 0.999 or _crossing_ratio(body_runs, x)[0] < 0.4

    hard_xs = [x for x in hard_xs
               if x <= bbox[0] + TOL or x >= bbox[2] - TOL or _is_column_rule(x)]
    header_candidates: list[float] = []
    for left, right, mid in _header_boundaries(layout, bbox, ys):
        if any(left < x < right for x in hard_xs):
            continue                                  # a real rule owns this gap
        if right - left > 80.0:
            # The boundary is the next label's start; body gutters may not line
            # up with it, so header placement is the only evidence needed.
            header_candidates.append(mid)
            continue
        # Body gutters need not align with a header gap (body text widths
        # differ), so accept the gap when no body text crosses it.
        if _crossing_ratio(body_runs, mid)[0] < 0.4:
            header_candidates.append(mid)

    boundaries = sorted(set(hard_xs) | set(header_candidates))
    soft_xs: list[float] = []
    internal_hard = [x for x in hard_xs if bbox[0] + TOL < x < bbox[2] - TOL]
    for left, right, candidate in ([] if len(internal_hard) >= 2 else
                                   _projection_boundaries(
                                       layout, bbox, ys, gap=params.cell_gap_pt)):
        if any(left < x < right for x in hard_xs):
            continue                                   # the real rule is the edge
        below = [x for x in boundaries if x < candidate]
        above = [x for x in boundaries if x > candidate]
        lo = below[-1] if below else bbox[0]
        hi = above[0] if above else bbox[2]
        width = hi - lo
        nearest = min((abs(candidate - x) for x in boundaries), default=0.0)
        if _header_words_between(layout, ys, lo, hi):
            continue                                   # header declares this column
        if width >= 12.0 and nearest >= 12.0:
            soft_xs.append(candidate)
    edges = [bbox[0], bbox[2]]
    all_xs = _unique(edges + hard_xs + header_candidates + soft_xs, 4.0)

    if len(all_xs) < 2 or len(ys) < 2:
        return TableGrid(bbox, all_xs, ys, source=region.source)

    nr, nc = len(ys) - 1, len(all_xs) - 1
    uf = _UnionFind(nr * nc)
    body_runs: dict[int, list[tuple[float, float]]] = {}

    for i in range(nr):
        for j in range(nc):
            index = i * nc + j
            if j + 1 < nc:
                boundary = all_xs[j + 1]
                is_hard = any(abs(boundary - x) <= TOL for x in hard_xs)
                if not is_hard:
                    continue                                  # logical soft split
                coverage = _coverage(component.vertical, boundary, ys[i], ys[i + 1])
                if coverage >= 0.55:
                    continue
                if i not in body_runs:
                    body_runs[i] = _word_runs(layout, ys[i], ys[i + 1],
                                              gap=params.cell_gap_pt)
                crossed = any(a <= boundary - 2.0 and b >= boundary + 2.0
                              for a, b in body_runs[i])
                if crossed:
                    uf.union(index, index + 1)
            if i + 1 < nr and ys[i + 1] in rule_ys:
                boundary = ys[i + 1]
                if _coverage(component.horizontal, boundary,
                             all_xs[j], all_xs[j + 1]) < 0.55:
                    uf.union(index, index + nc)

    groups: dict[int, list[tuple[int, int]]] = {}
    for i in range(nr):
        for j in range(nc):
            groups.setdefault(uf.find(i * nc + j), []).append((i, j))

    cells: list[GridCell] = []
    for members in groups.values():
        rows = [item[0] for item in members]
        columns = [item[1] for item in members]
        r0, r1, c0, c1 = min(rows), max(rows), min(columns), max(columns)
        cells.append(GridCell(r0, c0, r1 - r0 + 1, c1 - c0 + 1,
                              (all_xs[c0], ys[r0], all_xs[c1 + 1], ys[r1 + 1])))
    cells.sort(key=lambda cell: (cell.row, cell.column))
    grid = TableGrid(bbox, all_xs, ys, cells, source=region.source)
    _assign_words(layout, grid)
    return grid


def _column_centers(rows: list[list[TextWord]], gap: float) -> list[float]:
    starts: list[float] = []
    for row in rows:
        row_sorted = sorted(row, key=lambda w: w.bbox[0])
        if not row_sorted:
            continue
        starts.append(row_sorted[0].bbox[0])
        for previous, current in zip(row_sorted, row_sorted[1:]):
            if current.bbox[0] - previous.bbox[2] > gap:
                starts.append(current.bbox[0])
    if not starts:
        return []
    clusters: list[list[float]] = []
    for value in sorted(starts):
        if clusters and value - median(clusters[-1]) <= 6.0:
            clusters[-1].append(value)
        else:
            clusters.append([value])
    minimum_support = max(2, int(len(rows) * 0.4))
    return [sum(cluster) / len(cluster) for cluster in clusters
            if len(cluster) >= minimum_support]


def _alignment_grid(layout: PageLayout, region: TableRegion,
                    params: TableParams) -> TableGrid:
    rows = [list(row) for row in region.rows_words]
    if len(rows) < params.alignment_min_rows:
        return TableGrid(region.bbox, [], [], source=region.source)
    centers = _column_centers(rows, params.cell_gap_pt)
    if len(centers) < 2:
        return TableGrid(region.bbox, [], [], source=region.source)
    xs = [region.bbox[0]]
    xs += [(a + b) / 2.0 for a, b in zip(centers, centers[1:])]
    xs.append(region.bbox[2])
    ys = [region.bbox[1]]
    for previous, current in zip(rows, rows[1:]):
        prev_bottom = max(w.bbox[3] for w in previous)
        cur_top = min(w.bbox[1] for w in current)
        ys.append((prev_bottom + cur_top) / 2.0)
    ys.append(region.bbox[3])

    cells: list[GridCell] = []
    for row_index, row in enumerate(rows):
        row_sorted = sorted(row, key=lambda w: w.bbox[0])
        groups: list[list[TextWord]] = []
        for word in row_sorted:
            if groups and word.bbox[0] - max(w.bbox[2] for w in groups[-1]) <= params.cell_gap_pt:
                groups[-1].append(word)
            else:
                groups.append([word])
        for group in groups:
            left = min(w.bbox[0] for w in group)
            right = max(w.bbox[2] for w in group)
            center = (left + right) / 2.0
            column = min(range(len(centers)), key=lambda idx: abs(centers[idx] - center))
            bbox = (left, min(w.bbox[1] for w in group), right,
                    max(w.bbox[3] for w in group))
            cells.append(GridCell(row_index, column, 1, 1, bbox, _words_to_text(group),
                                  len(group)))
    return TableGrid(region.bbox, xs, ys, cells, source=region.source)


def recognize_structure(layout: PageLayout, region: TableRegion,
                        params: TableParams | None = None) -> TableGrid:
    params = params or TableParams()
    if region.component is not None:
        return _rule_grid(layout, region, params)
    return _alignment_grid(layout, region, params)


__all__ = ["GridCell", "RegionEvidence", "TableGrid", "TableRegion",
           "recognize_structure"]
