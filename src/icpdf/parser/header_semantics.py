"""Layer 4 - header and column semantics.

Header depth, per-column labels, coarse column roles and a table-type hypothesis
are inferred here.  None of these decisions can create or delete a table; a
region with no header is still reported (as a partial table) when it contains
structured numeric data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from icpdf.domain.candidate import ColumnRole
from icpdf.domain.table import TableType
from icpdf.parser.config import TableParams
from icpdf.parser.layout import PageLayout
from icpdf.parser.structure import GridCell, TableGrid, TableRegion

_NUMERIC = re.compile(r"^[<>±+\-–—]?\s*[\d.,]+\s*(?:[a-zA-Z%°Ω/]+)?$")
_WORD = re.compile(r"[a-z0-9]+")

_HEADER_WORDS = {
    "symbol", "parameter", "parameters", "min", "minimum", "typ", "typical",
    "nom", "nominal", "max", "maximum", "unit", "units", "condition",
    "conditions", "test", "tests", "value", "values", "limit", "limits",
    "device", "orderable", "package", "status", "description", "function",
    "pin", "pins", "name", "type", "reset", "bit", "bits", "field", "fields",
    "address", "register", "default", "signal", "signals", "temperature",
}

_TYPE_KEYWORDS: tuple[tuple[TableType, tuple[str, ...]], ...] = (
    (TableType.ABSOLUTE_MAXIMUM, ("absolute maximum", "absolute max", "esd ratings")),
    (TableType.RECOMMENDED_OPERATING, ("recommended operating", "recommended operation")),
    (TableType.ELECTRICAL_CHARACTERISTICS, ("electrical characteristics", "electrical spec",
                                            "noise measurement", "conversion timing",
                                            "timing requirements")),
    (TableType.THERMAL, ("thermal",)),
    (TableType.PIN_FUNCTIONS, ("pin function", "pin configuration", "pin description",
                               "signals and pins", "pin assignments")),
    (TableType.ORDERING_INFORMATION, ("ordering information", "orderable", "packaging information")),
)


@dataclass(frozen=True)
class HeaderSemantics:
    header_rows: int
    headers: list[str]
    column_roles: list[ColumnRole]
    title: str | None
    table_type: TableType


def _norm(text: str) -> str:
    return " ".join((text or "").casefold().split())


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall(_norm(text)))


def role_for_header(header: str | None) -> ColumnRole:
    """Map one header label to the frozen coarse role vocabulary.

    Token matching avoids the Phase 1.1 bug where ``administrator`` matched
    ``min`` by substring.
    """
    tokens = _tokens(header or "")
    if not tokens:
        return ColumnRole.UNKNOWN
    if tokens & {"min", "minimum"}:
        return ColumnRole.MIN
    if tokens & {"typ", "typical", "nom", "nominal"}:
        return ColumnRole.TYP
    if tokens & {"max", "maximum"}:
        return ColumnRole.MAX
    if tokens & {"unit", "units"}:
        return ColumnRole.UNIT
    if tokens & {"condition", "conditions", "test", "tests"}:
        return ColumnRole.CONDITION
    if tokens & {"symbol", "parameter", "parameters", "name", "signal", "signals"}:
        return ColumnRole.SYMBOL
    return ColumnRole.VALUE


def _is_numeric(text: str) -> bool:
    token = (text or "").strip()
    return bool(token) and bool(_NUMERIC.match(token))


def _row_cells(grid: TableGrid, row: int) -> list[GridCell]:
    return [cell for cell in grid.cells if cell.row == row]


def _nonempty(cells: list[GridCell]) -> list[GridCell]:
    return [cell for cell in cells if cell.text.strip()]


def _header_hits(cells: list[GridCell]) -> int:
    hits = 0
    for cell in cells:
        if _tokens(cell.text) & _HEADER_WORDS:
            hits += 1
    return hits


def _numeric_ratio(cells: list[GridCell]) -> float:
    nonempty = _nonempty(cells)
    if not nonempty:
        return 0.0
    return sum(1 for cell in nonempty if _is_numeric(cell.text)) / len(nonempty)


def _is_full_width(row: list[GridCell], n_columns: int) -> bool:
    return any(cell.column_span >= n_columns and cell.text.strip() for cell in row)


def _header_like(row: list[GridCell], n_columns: int) -> bool:
    nonempty = _nonempty(row)
    if not nonempty or _is_full_width(row, n_columns):
        return False
    if _header_hits(nonempty) >= 1:
        return True
    if _numeric_ratio(nonempty) >= 0.5:
        return False
    return all(len(cell.text.strip()) <= 40 for cell in nonempty)


def _is_sparse_lead(row: list[GridCell], n_columns: int) -> bool:
    """A leading row that labels only a few columns, e.g. "PGA GAIN = 4"
    sitting above a 13-column measurement grid.  It is header evidence when a
    full label row follows it."""
    nonempty = _nonempty(row)
    return (1 <= len(nonempty) < max(2, n_columns * 0.5)
            and not _is_full_width(row, n_columns)
            and all(len(cell.text.strip()) <= 40 for cell in nonempty))


def _is_label_row(row: list[GridCell], n_columns: int) -> bool:
    """Header rows name columns; value rows contain part numbers, numbers,
    or short status words.  A body row may mention "reset" once, so a label
    row needs two vocabulary hits or a merged (canopy) cell."""
    nonempty = _nonempty(row)
    if not nonempty or _is_full_width(row, n_columns):
        return False
    if any(len(cell.text.strip()) > 40 for cell in nonempty):
        return False
    return any(cell.column_span > 1 for cell in row) or _header_hits(nonempty) >= 2


def _infer_header_rows(grid: TableGrid) -> int:
    if grid.n_rows == 0:
        return 0
    first = _row_cells(grid, 0)
    if not _nonempty(first):
        return 0
    canopy = any(cell.column_span > 1 for cell in first)
    second = _row_cells(grid, 1) if grid.n_rows > 1 else []
    sparse_lead = _is_sparse_lead(first, grid.n_columns)
    if _header_hits(first) < 1 and not canopy and not (
            sparse_lead and _is_label_row(second, grid.n_columns)):
        return 0
    header_rows = 1
    if grid.n_rows < 2:
        return header_rows
    if _is_full_width(second, grid.n_columns):
        return header_rows
    # A section row ("OFFSET VOLTAGE" under the header) often merges into one
    # stray wide cell; it is body content, not a second header row.
    if len(_nonempty(second)) < 2:
        return header_rows
    if canopy or _is_label_row(second, grid.n_columns):
        header_rows = 2
    if header_rows >= 2 and grid.n_rows >= 3:
        third = _row_cells(grid, 2)
        second_canopy = any(cell.column_span > 1 for cell in second)
        if second_canopy and _is_label_row(third, grid.n_columns):
            header_rows = 3
    return min(header_rows, max(0, grid.n_rows - 1))


def _column_labels(grid: TableGrid, header_rows: int) -> list[str]:
    labels: list[str] = []
    for column in range(grid.n_columns):
        parts: list[str] = []
        for row in range(header_rows):
            for cell in _row_cells(grid, row):
                if cell.column <= column < cell.column + cell.column_span:
                    text = " ".join(cell.text.split())
                    if text and (not parts or parts[-1] != text):
                        parts.append(text)
                    break
        labels.append(" | ".join(parts))
    return labels


def _caption(layout: PageLayout, region: TableRegion, params: TableParams) -> str | None:
    candidates: list[tuple[float, str]] = []
    for block in layout.blocks:
        x0, y0, x1, y1 = block.bbox
        if y1 > region.bbox[1] + 2.0 or y1 < region.bbox[1] - 30.0:
            continue
        overlap = min(x1, region.bbox[2]) - max(x0, region.bbox[0])
        if overlap <= 0 or (x1 - x0) <= 0 or overlap / (x1 - x0) < 0.5:
            continue
        text = " ".join(line.text for line in block.lines).strip()
        if not text or len(text) > params.max_title_chars:
            continue
        if text.startswith(("•", "-", "(", "[")):
            continue
        candidates.append((y1, text))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def _infer_type(title: str | None, headers: list[str]) -> TableType:
    haystack = " ".join(x for x in (title or "", " ".join(headers)) if x).casefold()
    for table_type, keywords in _TYPE_KEYWORDS:
        if any(keyword in haystack for keyword in keywords):
            return table_type
    if any(headers):
        return TableType.OTHER
    return TableType.UNKNOWN


def infer_semantics(layout: PageLayout, region: TableRegion, grid: TableGrid,
                    params: TableParams | None = None) -> HeaderSemantics:
    params = params or TableParams()
    header_rows = _infer_header_rows(grid)
    headers = _column_labels(grid, header_rows)
    roles = [role_for_header(label) for label in headers]
    title = _caption(layout, region, params)
    if not title:
        joined = " / ".join(label for label in headers if label)
        title = joined or None
    return HeaderSemantics(header_rows, headers, roles, title,
                           _infer_type(title, headers))


def assess_region(grid: TableGrid, semantics: HeaderSemantics,
                  params: TableParams | None = None) -> tuple[bool, str | None]:
    """Evidence gate: reject graphics that are not tables without suppressing
    valid single-row tables."""
    params = params or TableParams()
    if grid.n_columns < 2 or grid.n_rows < 1 or not grid.cells:
        return False, "no multi-column grid"
    nonempty_rows = [row for row in range(grid.n_rows)
                     if len(_nonempty(_row_cells(grid, row))) >= 2]
    data_rows = grid.n_rows - semantics.header_rows
    if data_rows < 1:
        return False, "header without data rows"
    if len(nonempty_rows) < max(2, semantics.header_rows + 1):
        return False, "fewer than two populated rows"
    first = _row_cells(grid, 0)
    if semantics.header_rows == 0:
        numeric = sum(1 for cell in grid.cells if _is_numeric(cell.text))
        if numeric < params.min_numeric_cells:
            return False, "no header and too few numeric cells"
        if _numeric_ratio(first) >= 0.6:
            return False, "numeric first row resembles a bit-field diagram"
    texts = [cell.text.strip() for cell in grid.cells if cell.text.strip()]
    long_cells = sum(1 for text in texts if len(text) > params.max_cell_chars)
    if texts and long_cells / len(texts) > 0.5:
        return False, "prose-length text dominates the region"
    if grid.unassigned_words and len(grid.unassigned_words) > max(5, len(texts) * 0.25):
        return False, "text inside the region is not assignable to cells"
    return True, None


__all__ = ["HeaderSemantics", "assess_region", "infer_semantics", "role_for_header"]
