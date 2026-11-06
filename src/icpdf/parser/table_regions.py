"""Layer 2 - table region detection.

Proposes table regions from evidence, without deciding structure or semantics.

Ruled pages first collect physical :class:`RuleComponent` objects (Layer 1).
Components that share a column lattice and stack vertically with a title or
whitespace gap are aggregated into one :class:`TableRegion`; the merge,
absorption and implied outer boundary are all recorded as evidence.  A single
component remains exactly the region it always was, so Phase 1.2 detection is
unchanged.

On pages with no ruling at all, a strict baseline-alignment fallback keeps
text-only tables (including the synthetic fixtures) working.  Text-alignment
candidates are deliberately not proposed on ruled pages: that was the source of
the Phase 1.1 over-detection.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field

from icpdf.domain.common import BBox
from icpdf.parser.config import TableParams
from icpdf.parser.layout import PageLayout, RuleComponent
from icpdf.parser.structure import RegionEvidence, TableRegion
from icpdf.parser.text_blocks import TextWord

TOL = 2.5


def _bbox_union(boxes: list[BBox]) -> BBox:
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def _group_cells(words: list[TextWord], gap: float) -> list[list[TextWord]]:
    ordered = sorted(words, key=lambda w: w.bbox[0])
    groups: list[list[TextWord]] = []
    for word in ordered:
        if groups and word.bbox[0] - max(w.bbox[2] for w in groups[-1]) <= gap:
            groups[-1].append(word)
        else:
            groups.append([word])
    return groups


def _can_extend(current: list[list[TextWord]], words: list[TextWord],
                cells: list[list[TextWord]], last_bottom: float,
                median_h: float, params: TableParams) -> bool:
    modal = statistics.mode(len(row) for row in current) if current else len(cells)
    if abs(len(cells) - modal) > params.column_tolerance or len(cells) < 2:
        return False
    rows_box = _bbox_union([_bbox_union([w.bbox for w in row]) for row in current])
    row_box = _bbox_union([w.bbox for w in words])
    overlap = min(rows_box[2], row_box[2]) - max(rows_box[0], row_box[0])
    if overlap <= 0:
        return False
    return row_box[1] - last_bottom <= params.row_gap_factor * median_h


def _alignment_regions(layout: PageLayout, params: TableParams) -> list[TableRegion]:
    if not layout.row_bands:
        return []
    heights = [w.bbox[3] - w.bbox[1] for row in layout.row_bands for w in row
               if w.bbox[3] > w.bbox[1]]
    median_h = statistics.median(heights) if heights else 10.0
    regions: list[TableRegion] = []
    current: list[list[TextWord]] = []
    last_bottom = 0.0

    def close() -> None:
        nonlocal current
        if len(current) >= params.alignment_min_rows:
            rows = tuple(tuple(row) for row in current)
            bbox = _bbox_union([_bbox_union([w.bbox for w in row]) for row in current])
            regions.append(TableRegion(layout.page_number, bbox, "text_alignment",
                                       rows_words=rows,
                                       boundary_source="implied_alignment"))
        current = []

    for words in layout.row_bands:
        cells = _group_cells(words, params.cell_gap_pt)
        row_bbox = _bbox_union([w.bbox for w in words])
        if any(len(" ".join(w.text for w in cell)) > params.max_cell_chars
               for cell in cells):
            close()
            last_bottom = row_bbox[3]
            continue
        if len(cells) < 2:
            close()
            last_bottom = row_bbox[3]
            continue
        if current and not _can_extend(current, words, cells, last_bottom,
                                       median_h, params):
            close()
        current.append(words)
        last_bottom = row_bbox[3]
    close()
    return regions


def _component_columns(component: RuleComponent) -> list[float]:
    return sorted({round(segment.c, 2) for segment in component.vertical})


def _horizontal_extent(component: RuleComponent) -> tuple[float, float] | None:
    """The widest horizontal span of a component, i.e. its printed width."""
    if not component.horizontal:
        return None
    widest = max(component.horizontal, key=lambda segment: segment.length)
    return (widest.a, widest.b)


# A caption label starts a new table.  The signal is the document convention
# ("Table 6-28.", "Tabelle 6.28", "表 3"), not the font size: an in-table
# section band may be set at any size, and a caption may inherit the body size.
_CAPTION = re.compile(
    r"^\s*(?:table|tab\.?|tabelle|tabla|tableau|tabela|tabel|таблица|表|표"
    r"|figure|fig\.?|图)\b",
    re.IGNORECASE,
)


def _gap_has_caption(layout: PageLayout, y0: float, y1: float,
                     x0: float, x1: float) -> bool:
    """A caption label in the gap starts a new table, so do not merge.

    Only the label text is used.  Font size is deliberately ignored: section
    bands inside one table can be bold or larger, and captions in some
    templates are set at the body size.
    """
    if y1 - y0 <= 0:
        return False
    for block in layout.blocks:
        for span in block.spans:
            text = span.text.strip()
            if not text:
                continue
            if not (y0 - 1.0 <= span.bbox[1] and span.bbox[3] <= y1 + 1.0):
                continue
            cx = (span.bbox[0] + span.bbox[2]) / 2.0
            if not (x0 <= cx <= x1):
                continue
            if _CAPTION.match(text):
                return True
    return False


def _x_overlap_ratio(upper: RuleComponent, lower: RuleComponent) -> float:
    overlap = (min(upper.bbox[2], lower.bbox[2])
               - max(upper.bbox[0], lower.bbox[0]))
    width = min(upper.bbox[2] - upper.bbox[0],
                lower.bbox[2] - lower.bbox[0])
    if width <= 0:
        return 0.0
    return overlap / width


def _shared_columns(upper: RuleComponent, lower: RuleComponent,
                    tol: float) -> list[float]:
    lower_columns = _component_columns(lower)
    return [column for column in _component_columns(upper)
            if any(abs(column - other) <= tol for other in lower_columns)]


def _merge_pair(layout: PageLayout, upper: RuleComponent, lower: RuleComponent,
                gap: float, params: TableParams
                ) -> tuple[bool, dict | None, str | None]:
    """Structural test for merging two vertically adjacent components."""
    if _x_overlap_ratio(upper, lower) < params.merge_min_x_overlap_ratio:
        return False, None, "components do not overlap horizontally"
    upper_columns = _component_columns(upper)
    lower_columns = _component_columns(lower)
    shared = _shared_columns(upper, lower, params.merge_column_tol_pt)
    if len(shared) < params.merge_min_shared_columns:
        return False, None, "components share fewer than two column rules"
    if (len(shared) / len(upper_columns) < params.merge_shared_ratio
            or len(shared) / len(lower_columns) < params.merge_shared_ratio):
        return False, None, "column lattices differ"
    upper_extent = _horizontal_extent(upper)
    lower_extent = _horizontal_extent(lower)
    if upper_extent is None or lower_extent is None:
        return False, None, "component has no horizontal rule extent"
    if (abs(upper_extent[0] - lower_extent[0]) > params.merge_extent_tol_pt
            or abs(upper_extent[1] - lower_extent[1]) > params.merge_extent_tol_pt):
        return False, None, "horizontal rule extents do not align"
    gap_x0 = min(upper.bbox[0], lower.bbox[0],
                 upper_extent[0], lower_extent[0])
    gap_x1 = max(upper.bbox[2], lower.bbox[2],
                 upper_extent[1], lower_extent[1])
    if _gap_has_caption(layout, upper.bbox[3], lower.bbox[1],
                        gap_x0, gap_x1):
        return False, None, "gap contains a table/figure caption"
    evidence = {
        "shared": tuple(shared),
        "gap": gap,
        "extents": (min(upper_extent[0], lower_extent[0]),
                    max(upper_extent[1], lower_extent[1])),
    }
    return True, evidence, None


@dataclass
class _Cluster:
    members: list[RuleComponent] = field(default_factory=list)
    evidence: list[RegionEvidence] = field(default_factory=list)

    @property
    def bottom(self) -> float:
        return max(member.bbox[3] for member in self.members)


def _cluster_components(layout: PageLayout, components: list[RuleComponent],
                        params: TableParams) -> list[_Cluster]:
    ordered = sorted(components, key=lambda c: (round(c.bbox[1], 1),
                                                round(c.bbox[0], 1)))
    clusters: list[_Cluster] = []
    for component in ordered:
        for cluster in clusters:
            gap = component.bbox[1] - cluster.bottom
            if gap < params.merge_min_gap_pt or gap > params.merge_max_gap_pt:
                continue
            seed = cluster.members[0]
            merged, evidence, _ = _merge_pair(layout, seed, component,
                                              gap, params)
            if not merged:
                continue
            cluster.members.append(component)
            cluster.evidence.append(RegionEvidence(
                "merge",
                (f"component {seed.component_id} and component "
                 f"{component.component_id} share {len(evidence['shared'])} "
                 f"column rule(s) across a {gap:.1f}pt band"),
                (seed.component_id, component.component_id),
                tuple(evidence["shared"]) + (gap,),
            ))
            cluster.evidence.append(RegionEvidence(
                "absorbed",
                (f"component {component.component_id} is emitted through "
                 f"region seed {seed.component_id}"),
                (component.component_id,),
            ))
            break
        else:
            clusters.append(_Cluster([component], []))
    return clusters


def _union_component(page_number: int, members: list[RuleComponent],
                     bbox: BBox) -> RuleComponent:
    horizontal = tuple(segment for member in members
                       for segment in member.horizontal)
    vertical = tuple(segment for member in members
                     for segment in member.vertical)
    primitives = tuple(primitive for member in members
                       for primitive in member.primitives)
    indices = tuple(sorted({index for member in members
                            for index in member.primitive_indices}))
    return RuleComponent(bbox, horizontal, vertical, primitives, indices,
                         page_number, -1)


def _region_from_cluster(layout: PageLayout, cluster: _Cluster) -> TableRegion:
    members = cluster.members
    bbox = _bbox_union([member.bbox for member in members])
    evidence = list(cluster.evidence)
    boundary_source = "ruled"
    if len(members) > 1:
        extents = [extent for member in members
                   if (extent := _horizontal_extent(member)) is not None]
        if extents:
            left = statistics.median(extent[0] for extent in extents)
            right = statistics.median(extent[1] for extent in extents)
            if left < bbox[0] - TOL or right > bbox[2] + TOL:
                bbox = (max(layout.rect[0], min(bbox[0], left)),
                        bbox[1],
                        min(layout.rect[2], max(bbox[2], right)),
                        bbox[3])
                boundary_source = "implied_horizontal"
                evidence.append(RegionEvidence(
                    "implied_outer",
                    (f"left/right boundaries {left:.1f}/{right:.1f} come from "
                     "the common horizontal-rule extent"),
                    tuple(member.component_id for member in members),
                    (left, right),
                ))
    component = (_union_component(layout.page_number, members, bbox)
                 if len(members) > 1 else members[0])
    return TableRegion(
        page_number=layout.page_number,
        bbox=bbox,
        source="rule_lattice",
        component=component,
        components=tuple(members),
        boundary_source=boundary_source,
        evidence=tuple(evidence),
    )


def detect_table_regions(layout: PageLayout,
                         params: TableParams | None = None) -> list[TableRegion]:
    params = params or TableParams()
    regions = [_region_from_cluster(layout, cluster)
               for cluster in _cluster_components(layout, layout.components,
                                                  params)]
    if not layout.components:
        regions.extend(_alignment_regions(layout, params))
    regions.sort(key=lambda region: (round(region.bbox[1], 1), round(region.bbox[0], 1)))
    return regions


__all__ = ["detect_table_regions"]
