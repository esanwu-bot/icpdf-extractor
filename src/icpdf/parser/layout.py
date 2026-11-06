"""Layer 1 - page layout analysis.

Collects the three deterministic inputs later layers operate on: text words,
baseline row bands, and connected components of thin vector ruling.  This module
makes no table decision.  Ruling primitives and their connectivity live in
:mod:`icpdf.parser.rule_primitives`; the helpers here keep the historical
``page_segments`` / ``rule_components`` entry points.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median

from icpdf.domain.common import BBox
from icpdf.parser.coords import PageGeometry
from icpdf.parser.rule_primitives import (
    GRID_TOL,
    RuleComponent,
    RulePrimitive,
    RuleSegment,
    build_components,
    collect_primitives,
    merge_primitives,
)
from icpdf.parser.text_blocks import TextBlock, TextWord


@dataclass(frozen=True)
class PageLayout:
    page_number: int
    rect: BBox
    blocks: list[TextBlock]
    words: list[TextWord]
    row_bands: list[list[TextWord]]
    components: list[RuleComponent]


def page_segments(page, geometry: PageGeometry | None = None, *,
                  page_number: int = 1) -> list[RuleSegment]:
    """Collinear-merged horizontal/vertical ruling, including quad edges."""
    primitives = collect_primitives(page, page_number, geometry)
    return [segment for segment, _ in merge_primitives(primitives)]


def rule_components(page, geometry: PageGeometry | None = None, *,
                    tol: float = GRID_TOL,
                    min_width: float = 70.0,
                    min_height: float = 15.0,
                    page_number: int = 1) -> list[RuleComponent]:
    """Connected components of ruling; each dense component may be a table."""
    primitives = collect_primitives(page, page_number, geometry)
    return build_components(primitives, page_number=page_number, tol=tol,
                            min_width=min_width, min_height=min_height)


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
                                  min_height=min_rule_height,
                                  page_number=page_number)
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


__all__ = ["PageLayout", "RuleComponent", "RulePrimitive", "RuleSegment",
           "analyze_layout", "page_segments", "rule_components"]
