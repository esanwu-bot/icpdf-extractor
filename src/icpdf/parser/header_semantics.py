"""Layer 4 - header and column semantics.

Header depth, per-column labels, coarse column roles and a table-type hypothesis
are inferred here.  None of these decisions can create or delete a table; a
region with no header is still reported (as a partial table) when it contains
structured numeric data or a ruled short-label/description grid (tape
dimension codes and similar headerless key tables).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from icpdf.domain.candidate import ColumnRole
from icpdf.domain.common import BBox
from icpdf.domain.table import TableType
from icpdf.parser.config import TableParams
from icpdf.parser.layout import PageLayout
from icpdf.parser.structure import GridCell, TableGrid, TableRegion

_NUMERIC = re.compile(r"^[<>±+\-–—]?\s*[\d.,]+\s*(?:[a-zA-Z%°Ω/]+)?$")
_WORD = re.compile(r"[a-z0-9]+")
_DOT_LEADER = re.compile(r"\.{4,}|…{2,}")

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
class HeaderCellRef:
    """One printed header cell behind one column label."""

    level: int
    column: int
    text: str
    bbox: BBox
    source_row: int
    source_column: int


@dataclass(frozen=True)
class HeaderSemantics:
    header_rows: int
    headers: list[str]
    column_roles: list[ColumnRole]
    title: str | None
    table_type: TableType
    header_path: list[list[str]] = field(default_factory=list)
    header_cells: list[HeaderCellRef] = field(default_factory=list)


def _norm(text: str) -> str:
    return " ".join((text or "").casefold().split())


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall(_norm(text)))


_LEADING_NON_SYMBOL = {"orderable", "part", "number", "parts", "address", "bit",
                       "sample", "samples", "code"}
_UNIT_WORDS = {"v", "mv", "kv", "a", "ma", "ua", "w", "mw", "hz", "khz", "mhz",
               "ghz", "ns", "us", "ms", "ps", "s", "ohm", "ohms", "kohm", "db",
               "dbm", "c", "f", "pf", "nf", "uf"}
# Device/package variant columns (e.g. "D (SOIC) | 8 PINS") are conditions of
# the measurement; a bare "PACKAGE" column is an attribute and stays VALUE.
_PACKAGE_WORDS = {"soic", "vssop", "pdip", "tssop", "sot", "lccc", "cdip",
                  "qfn", "vqfn", "wqfn", "bga", "ssop", "msop", "dip", "sop", "so"}


def role_for_header(header: str | None) -> ColumnRole:
    """Map one header label to the frozen coarse role vocabulary.

    Token matching avoids the Phase 1.1 bug where ``administrator`` matched
    ``min`` by substring.
    """
    tokens = _tokens(header or "")
    if not tokens:
        return ColumnRole.UNKNOWN
    # A metric name may contain a limit word ("MAXIMUM SAMPLING RATE",
    # "NOMINAL BANDWIDTH ..."); only a short label names the column itself.
    if len(tokens) <= 2 and tokens & {"min", "minimum"}:
        return ColumnRole.MIN
    if len(tokens) <= 3 and tokens & {"typ", "typical", "nom", "nominal"}:
        return ColumnRole.TYP
    if len(tokens) <= 2 and tokens & {"max", "maximum"}:
        return ColumnRole.MAX
    if tokens & {"unit", "units"}:
        return ColumnRole.UNIT
    if tokens & {"condition", "conditions", "test", "tests"}:
        return ColumnRole.CONDITION
    # A bare MODE names a selector; "NORMAL MODE" is a value entry.
    if tokens == {"mode"} or tokens & {"source", "clause", "configured", "derived"}:
        return ColumnRole.CONDITION
    if len(tokens) >= 4 and tokens & _PACKAGE_WORDS:
        return ColumnRole.CONDITION
    if tokens & {"symbol", "parameter", "parameters", "signal", "signals", "acronym"}:
        return ColumnRole.SYMBOL
    return ColumnRole.VALUE


def _leading_role(header: str, role: ColumnRole) -> ColumnRole:
    """The first column of a datasheet table names the parameter row.

    Part-number, address, bit-index and sample-code columns are the
    exceptions; everything else that is not an explicit min/typ/max/unit
    column is a symbol column, including tables whose leading header cell is
    empty.
    """
    if role not in (ColumnRole.VALUE, ColumnRole.UNKNOWN):
        return role
    if _tokens(header) & _LEADING_NON_SYMBOL:
        return role
    # "fCLK (MHz)" names a test stimulus, i.e. a condition column.
    for inner in re.findall(r"\(([^)]*)\)", _norm(header)):
        if _tokens(inner) & _UNIT_WORDS:
            return ColumnRole.CONDITION
    return ColumnRole.SYMBOL


def _is_numeric(text: str) -> bool:
    token = (text or "").strip()
    return bool(token) and bool(_NUMERIC.match(token))


_LABEL_MAX_CHARS = 12
_LABEL_PUNCTUATION = ".:;!?,"


def _is_short_label(text: str) -> bool:
    token = (text or "").strip()
    if not token or len(token) > _LABEL_MAX_CHARS:
        return False
    return len(token.split()) <= 2 and not any(ch in token for ch in _LABEL_PUNCTUATION)


def _is_label_grid(grid: TableGrid) -> bool:
    """A fully ruled key/description grid (e.g. tape dimension codes) is a
    table without a header row or numeric values.  Drawings and prose fail
    because their rows are sparse or their leading cell is a sentence."""
    if grid.source != "rule_lattice" or grid.n_rows < 3 or grid.n_columns < 2:
        return False
    populated: list[list[GridCell]] = []
    for row in range(grid.n_rows):
        cells = _nonempty(_row_cells(grid, row))
        if len(cells) >= 2:
            populated.append(cells)
        elif cells:
            return False                      # sparse label band, not a grid
    if len(populated) < 3:
        return False
    for cells in populated:
        leading = min(cells, key=lambda cell: cell.column)
        if leading.column != 0 or leading.column_span != 1:
            return False
        if not _is_short_label(leading.text):
            return False
        if len(_nonempty(_row_cells(grid, leading.row))) < 2:
            return False
    return True


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


def _is_ordinal_header(row: list[GridCell]) -> bool:
    """``OCTET | 0 | 1 | ...`` or ``NIBBLE | 0 | 1 | ...`` - the two-row
    ordinal header used by register maps.  The label cell is text and the
    rest is a complete 0-based run."""
    ordered = sorted(_nonempty(row), key=lambda cell: cell.column)
    if len(ordered) < 3:
        return False
    label = ordered[0].text.strip()
    if not label or any(ch.isdigit() for ch in label):
        return False
    values = [cell.text.strip() for cell in ordered[1:]]
    return values == [str(index) for index in range(len(values))]


def _is_tabular_first_row(row: list[GridCell], n_columns: int) -> bool:
    """A first row that labels most columns with short, non-numeric text.

    This catches real headers whose vocabulary is outside ``_HEADER_WORDS``
    (e.g. "MODE OF OPERATION", "LETTER IDENTIFIER", "PARTS").  Bit-field
    rows ("OCTET", 0, 1, ...) stay out because they are mostly numeric, and
    data rows rarely label half of the columns with alphabetic text.
    """
    nonempty = _nonempty(row)
    if len(nonempty) < 2 or len(nonempty) * 2 <= n_columns:
        return False
    if _is_full_width(row, n_columns):
        return False
    if any(len(cell.text.strip()) > 40 for cell in nonempty):
        return False
    if _numeric_ratio(nonempty) >= 0.4:
        return False
    alpha = sum(1 for cell in nonempty if any(ch.isalpha() for ch in cell.text))
    return alpha >= 2


def _looks_like_toc(grid: TableGrid) -> bool:
    """Tables of contents and index lists use dot leaders; they are not data
    tables even when their leader dots form a stable column lattice."""
    texts = [cell.text.strip() for cell in grid.cells if cell.text.strip()]
    if not texts:
        return False
    hits = sum(1 for text in texts if _DOT_LEADER.search(text))
    return hits >= max(2, int(len(texts) * 0.3))


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
    ordinal_pair = _is_ordinal_header(first) and _is_ordinal_header(second)
    # A label that spans two header bands (rows 0-1) is itself evidence of a
    # two-row header, e.g. "OPTIMAL SYSREF_SEL SETTING" beside a group label.
    first_span = max((cell.row_span for cell in first if cell.text.strip()), default=1)
    if not (_header_hits(first) >= 1 or canopy
            or _is_tabular_first_row(first, grid.n_columns)
            or first_span > 1
            or (sparse_lead and _is_label_row(second, grid.n_columns))
            or ordinal_pair):
        return 0
    header_rows = max(1, min(first_span, grid.n_rows - 1))
    if grid.n_rows < 2:
        return header_rows
    if ordinal_pair:
        return min(2, max(0, grid.n_rows - 1))
    if _is_full_width(second, grid.n_columns):
        return header_rows
    # A section row ("OFFSET VOLTAGE" under the header) often merges into one
    # stray wide cell; it is body content, not a second header row.
    if len(_nonempty(second)) < 2:
        return header_rows
    if canopy or _is_label_row(second, grid.n_columns):
        header_rows = max(header_rows, 2)
    if header_rows >= 2 and grid.n_rows >= 3:
        third = _row_cells(grid, 2)
        second_canopy = any(cell.column_span > 1 for cell in second)
        # Pin counts ("8 PINS") repeat across the data columns and belong to
        # the header; a lone section banner ("Read Only ID Registers") does not.
        third_labels = _nonempty(third)
        if (second_canopy or _is_label_row(second, grid.n_columns)) \
                and len(third_labels) >= max(2, grid.n_columns // 2) \
                and _is_label_row(third, grid.n_columns):
            header_rows = 3
    return min(header_rows, max(0, grid.n_rows - 1))


def _nearest_canopy(grid: TableGrid, row: int, column: int) -> str:
    """Label for a header column left blank under a shared canopy.

    Datasheets often draw "REGISTER BITS" over the middle of a bit range but
    mean it for every bit column; the nearest multi-column label is the best
    evidence we have.
    """
    centre = (grid.xs[column] + grid.xs[column + 1]) / 2.0
    best: tuple[float, GridCell] | None = None
    for cell in _row_cells(grid, row):
        if cell.column_span <= 1:
            continue
        text = " ".join(cell.text.split())
        if not text:
            continue
        distance = abs((cell.bbox[0] + cell.bbox[2]) / 2.0 - centre)
        if best is None or distance < best[0]:
            best = (distance, cell)
    if best is None:
        return ""
    cell = best[1]
    low, high = cell.column, cell.column + cell.column_span - 1
    between = (range(column + 1, low) if column < low
               else range(high + 1, column) if column > high else ())
    # A labelled header cell between this column and the canopy starts a new
    # header section: the canopy does not reach past it.
    for middle in between:
        if any(other.column <= middle < other.column + other.column_span
               and other.text.strip() for other in _row_cells(grid, row)):
            return ""
    return " ".join(cell.text.split())


def _row_labels(grid: TableGrid, row: int) -> dict[int, str]:
    labels: dict[int, str] = {}
    for cell in _row_cells(grid, row):
        text = " ".join(cell.text.split())
        if not text:
            continue
        for column in range(cell.column, cell.column + cell.column_span):
            labels[column] = text
    return labels


def _centered_group_labels(grid: TableGrid, row: int) -> dict[int, str]:
    """Spread a group label centred over its columns to the unlabelled ones.

    ``PGA GAIN = 4`` is drawn in the middle column of a five-column block; the
    block edges are the midpoints between neighbouring labels, mirrored at the
    row ends.  A single label expands symmetrically while both flanks are free.
    """
    cells = [cell for cell in _row_cells(grid, row) if cell.text.strip()]
    if not cells or any(cell.column_span > 1 for cell in cells):
        return {}
    labels = _row_labels(grid, row)
    centres = [((cell.bbox[0] + cell.bbox[2]) / 2.0, cell) for cell in cells]
    centres.sort(key=lambda item: item[0])
    spans: list[tuple[float, float, str]] = []
    for index, (centre, cell) in enumerate(centres):
        if len(centres) == 1:
            half = (cell.bbox[2] - cell.bbox[0]) / 2.0
        elif index == 0:
            half = (centres[1][0] - centre) / 2.0
        elif index == len(centres) - 1:
            half = (centre - centres[index - 1][0]) / 2.0
        else:
            half = 0.0
        if len(centres) > 1 and 0 < index < len(centres) - 1:
            spans.append(((centre + centres[index - 1][0]) / 2.0,
                          (centre + centres[index + 1][0]) / 2.0,
                          " ".join(cell.text.split())))
        else:
            spans.append((centre - half, centre + half, " ".join(cell.text.split())))
    spread: dict[int, str] = {}
    for column in range(grid.n_columns):
        if column in labels:
            continue
        centre = (grid.xs[column] + grid.xs[column + 1]) / 2.0
        for low, high, text in spans:
            if low <= centre <= high:
                spread[column] = text
                break
    if len(centres) == 1 and not spread:
        # A lone label with no neighbours still covers a symmetric block.
        first = centres[0][1]
        low, high = first.column, first.column + first.column_span - 1
        while low > 0 and high + 1 < grid.n_columns:
            low -= 1
            high += 1
        for column in range(low, high + 1):
            if column not in labels:
                spread[column] = " ".join(first.text.split())
    return spread


def _ordinal_group_labels(grid: TableGrid, row: int,
                          next_row: dict[int, str]) -> dict[int, str]:
    """Spread ``OCTET | 0..7`` over an ``NIBBLE | 0..15`` row.

    The group labels are centred over their column pairs, but the drawn rules
    may or may not split the label cell.  When the labels form a complete
    numeric run and divide the data columns evenly, that division is the
    intended attribution.
    """
    cells = [cell for cell in _row_cells(grid, row)
             if cell.column > 0 and cell.text.strip()]
    if len(cells) < 2:
        return {}
    ordered = sorted(cells, key=lambda cell: cell.column)
    values = [cell.text.strip() for cell in ordered]
    if values != [str(index) for index in range(len(values))]:
        return {}
    below = [next_row.get(column, "") for column in range(1, grid.n_columns)]
    if any(not text for text in below) or any(not text.isdigit() for text in below):
        return {}
    data_columns = grid.n_columns - 1
    if data_columns % len(ordered):
        return {}
    width = data_columns // len(ordered)
    return {1 + index * width + offset: label
            for index, label in enumerate(values)
            for offset in range(width)}


def _header_label_rows(grid: TableGrid, header_rows: int) -> list[dict[int, str]]:
    raw = [_row_labels(grid, row) for row in range(header_rows)]
    # The leading column is the row-header column; a canopy over the data
    # columns (a device list, say) does not label it even when it is blank
    # on the canopy row.
    row_header = any(labels.get(0) for labels in raw[1:])
    rows: list[dict[int, str]] = []
    for row, labels in enumerate(raw):
        labels = dict(labels)
        ordinal = (_ordinal_group_labels(grid, row, raw[row + 1])
                   if row + 1 < header_rows else {})
        if ordinal:
            labels.update(ordinal)
        elif any(cell.column_span > 1 and cell.text.strip()
                 for cell in _row_cells(grid, row)):
            for column in range(grid.n_columns):
                if column in labels:
                    continue
                if column == 0 and row_header:
                    continue
                text = _nearest_canopy(grid, row, column)
                if text:
                    labels[column] = text
        else:
            for column, text in _centered_group_labels(grid, row).items():
                labels.setdefault(column, text)
        rows.append(labels)
    return rows


def _column_label_parts(grid: TableGrid, header_rows: int) -> list[list[str]]:
    rows = _header_label_rows(grid, header_rows)
    paths: list[list[str]] = []
    for column in range(grid.n_columns):
        parts: list[str] = []
        for labels in rows:
            text = labels.get(column, "")
            if text:
                # Repeated labels are meaningful across levels (OCTET 0 is
                # also NIBBLE 0), so levels are never collapsed.
                parts.append(text)
        paths.append(parts)
    return paths


def _source_header_cell(grid: TableGrid, level: int, column: int,
                        text: str) -> GridCell | None:
    """Printed cell that carries ``text`` for ``column`` at ``level``.

    Canopies and centred group labels can be spread beyond their drawn cell,
    so a direct hit is preferred, then the nearest cell with the same text.
    """
    normalized = " ".join(text.split())
    direct = [cell for cell in grid.cells
              if cell.row <= level < cell.row + cell.row_span
              and cell.column <= column < cell.column + cell.column_span
              and " ".join(cell.text.split()) == normalized]
    if direct:
        return direct[0]
    centre = (grid.xs[column] + grid.xs[column + 1]) / 2.0
    best: tuple[float, GridCell] | None = None
    for cell in grid.cells:
        if cell.row != level or not cell.text.strip():
            continue
        if " ".join(cell.text.split()) != normalized:
            continue
        distance = abs((cell.bbox[0] + cell.bbox[2]) / 2.0 - centre)
        if best is None or distance < best[0]:
            best = (distance, cell)
    return best[1] if best else None


def _header_cell_refs(grid: TableGrid, rows: list[dict[int, str]]
                      ) -> list[HeaderCellRef]:
    refs: list[HeaderCellRef] = []
    for level, labels in enumerate(rows):
        for column, text in sorted(labels.items()):
            cell = _source_header_cell(grid, level, column, text)
            if cell is None:
                continue
            refs.append(HeaderCellRef(level=level, column=column, text=text,
                                      bbox=cell.bbox, source_row=cell.row,
                                      source_column=cell.column))
    return refs


def _column_labels(grid: TableGrid, header_rows: int) -> list[str]:
    return [" | ".join(parts)
            for parts in _column_label_parts(grid, header_rows)]


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
    label_rows = _header_label_rows(grid, header_rows)
    header_path = _column_label_parts(grid, header_rows)
    header_cells = _header_cell_refs(grid, label_rows)
    headers = [" | ".join(parts) for parts in header_path]
    roles = [role_for_header(label) for label in headers]
    if roles:
        roles[0] = _leading_role(headers[0], roles[0])
    # An unlabeled column sitting left of the limit columns carries the test
    # conditions (datasheets leave that header blank).
    for column in range(1, len(roles)):
        if roles[column] != ColumnRole.UNKNOWN:
            continue
        if any(role in (ColumnRole.MIN, ColumnRole.TYP, ColumnRole.MAX)
               for role in roles[column + 1:]):
            roles[column] = ColumnRole.CONDITION
    title = _caption(layout, region, params)
    if not title:
        joined = " / ".join(label for label in headers if label)
        title = joined or None
    return HeaderSemantics(header_rows, headers, roles, title,
                           _infer_type(title, headers), header_path,
                           header_cells)


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
    if _looks_like_toc(grid):
        return False, "dot-leader contents list"
    first = _row_cells(grid, 0)
    if semantics.header_rows == 0:
        numeric = sum(1 for cell in grid.cells if _is_numeric(cell.text))
        if numeric < params.min_numeric_cells and not _is_label_grid(grid):
            return False, "no header and too few numeric cells"
        # Only shallow all-numeric grids are bit-field diagrams; register maps
        # ("OCTET / NIBBLE" grids) can also start with numbers but span many
        # rows and are tables.
        if grid.n_rows <= 4 and _numeric_ratio(first) >= 0.6:
            return False, "numeric first row resembles a bit-field diagram"
    texts = [cell.text.strip() for cell in grid.cells if cell.text.strip()]
    long_cells = sum(1 for text in texts if len(text) > params.max_cell_chars)
    if texts and long_cells / len(texts) > 0.5:
        return False, "prose-length text dominates the region"
    if grid.unassigned_words and len(grid.unassigned_words) > max(5, len(texts) * 0.25):
        return False, "text inside the region is not assignable to cells"
    return True, None


__all__ = ["HeaderSemantics", "assess_region", "infer_semantics", "role_for_header"]
