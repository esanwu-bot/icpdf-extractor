# Phase 1.4 S2b — Logical Boundary Lattice and Projection

**Status:** design proposal only (revision r2, based on `cf59799`). No
implementation, schema change, Gold change or pipeline integration is authorized
by this document. Implementation starts only after the Reviewer closes the
items in §1.

**Relationship to the approved S2 design:** `docs/PHASE1_4_S2.md` remains the
umbrella design. S2b narrows its §5–§7 to the logical column lattice and the
physical→logical projection. Where this document is more specific, it is a
proposal for review, not a replacement of the approved principles.

## 1. Review resolution map

This revision answers the seven review items and the P0/P1 findings on
`cf59799`. Nothing below is an implementation claim; every repository statement
is backed by a path and line reference in §3.

| Item | Question | Answer in |
| --- | --- | --- |
| R1 | Actual repository definitions of `DetectedTable`, `DetectedCell`, `DetectedHeaderCell`, `grid.xs`, `region_components` | §3.1–§3.3 |
| R2 | Gold v2 annotation version, item count, logical fields, and 67 vs 65 | §3.6, §12.1 |
| R3 | How `PhysicalColumnOverlap` locates a physical column across regions | §3.3, §7.1 |
| R4 | Minimum evidence fields per boundary source and validator rejection rules | §5.3, §11 |
| R5 | No-evidence demotion vs condition-path demotion | §6.5 |
| R6 | Preserving `table-params/v1` SHA and S2a audit compatibility | §5.8 |
| R7 | Independently reconstructable physical-cell and word assignment | §5.6, §9 |
| P0-1 | Region-local lattices vs a global `grid.xs` index | §3.3, §7.1 |
| P0-2 | Missing `subrule_promoted` / outer-edge evidence kinds | §5.3 |
| P0-3 | Every demotion incorrectly assigned to `condition_path` | §6.5 |
| P0-4 | `table-params/v2` without version-dispatched serialization | §5.8 |
| P1-1 | Which words of a shared physical cell belong to which logical cell | §5.6, §9.3 |
| P1-2 | Duplicate `projection` / `column_projection` | §5.4, §5.7 |
| P1-3 | Invented role-source vocabulary | §5.5 |
| P1-4 | Ambiguous `visual_columns` index | §5.4 |
| P1-5 | Gold `ambiguous` conflated with algorithm `unresolved` | §12.2 |

## 2. Problem

S2a established that the visual boundary evidence is trustworthy: every
persisted segment resolves to real PDF primitives. S2b addresses a different
question:

> Which printed and structural facts justify treating a boundary as a logical
> column boundary, and how are physical cells projected onto those logical
> columns without changing the physical grid?

The two lattices are not interchangeable. Gold v2 contains tables where logical
columns exceed visual columns (header canopies) and tables where visual columns
exceed logical columns (body condition sub-rules). The current logical count is
18/21 on the 21 typed Gold v2 tables; S2b must make the reasoning explicit and
auditable rather than infer a count from cell content.

Gold v1 (46 tables) does **not** carry typed logical columns. It therefore
contributes physical/S2a/candidate regression data and a set of explicitly
ambiguous cases, but it is not a logical-column ground truth. This distinction
is developed in §3.6 and §12.

Success means:

- every kept logical boundary has at least one allowed, resolvable evidence
  source;
- every logical column carries a traceable physical-column projection using the
  table's one physical lattice;
- every logical cell carries physical cell references and a disjoint per-cell
  word partition;
- undecidable cases fail closed at table level instead of guessing;
- S1 physical fields and S2a visual fields are byte-for-byte unchanged.

## 3. Repository facts (R1, R3)

### 3.1 Actual parser models

These are the current definitions, not proposed models. Excerpts are abridged
to fields only; the source is authoritative.

`src/icpdf/parser/table_detector.py:29`:

```python
class DetectedCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    text: str
    bbox: BBox
    column_index: int = Field(ge=0)
    row_span: int = Field(default=1, ge=1)
    column_span: int = Field(default=1, ge=1)
```

`src/icpdf/parser/table_detector.py:38`:

```python
class DetectedRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    bbox: BBox
    cells: list[DetectedCell]
    grid_row: int = Field(default=0, ge=0)
```

`src/icpdf/parser/table_detector.py:45`:

```python
class DetectedHeaderCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    level: int = Field(ge=0)
    column: int = Field(ge=0)
    text: str
    bbox: BBox
    source_row: int = Field(ge=0)
    source_column: int = Field(ge=0)
```

`src/icpdf/parser/table_detector.py:55`:

```python
class DetectedTable(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    page_number: int = Field(ge=1)
    bbox: BBox
    title: str | None = None
    table_type: TableType = TableType.UNKNOWN
    headers: list[str] = Field(default_factory=list)
    header_rows: int = Field(default=0, ge=0)
    header_path: list[list[str]] = Field(default_factory=list)
    header_cells: list[DetectedHeaderCell] = Field(default_factory=list)
    column_roles: list[str] = Field(default_factory=list)
    rows: list[DetectedRow] = Field(default_factory=list)
    detection_method: str = "text_alignment"
    confidence: float = Field(ge=0.0, le=1.0)
    reconstruction_status: ReconstructionStatus
    uncertainty_reason: str | None = None
    region_components: list[int] = Field(default_factory=list)
    boundary_source: str = "ruled"
    merge_evidence: list[str] = Field(default_factory=list)
    # Phase 1.4 S2a - derived visual lattice; never affects the physical grid.
    visual_boundaries: tuple[float, ...] = ()
    visual_boundary_status: str = "unknown"
    visual_columns: int | None = None
    partial_boundaries: tuple[float, ...] = ()
    visual_boundary_evidence: tuple[VisualBoundary, ...] = ()
```

Consequences that the design must respect:

- `DetectedCell` has **no** `cell_id`; its parser-level identity is
  `(DetectedRow.grid_row, index within DetectedRow.cells)`.
- `DetectedHeaderCell` has **no** `header_cell_id`; its parser-level identity is
  `(level, column, source_row, source_column)`.
- `DetectedTable` does **not** persist `grid.xs`, `grid.ys`, or per-cell word
  ids. Those exist only in the intermediate `TableGrid` / `TextWord` objects
  during `detect_tables()`.
- `DetectedTable.column_roles` is the existing per-physical-column role list
  from `infer_semantics`; S2b logical roles must not overwrite it.

Domain models add ids during rebuild (`src/icpdf/parser/table_rebuilder.py`):

- `table_id = f"p{page:03d}-t{table_index:02d}"`;
- `row_id = f"{table_id}-r{row_index:02d}"`;
- `cell_id = f"{row_id}-c{column:02d}"`;
- `header_cell_id = f"{table_id}-h{level:02d}-c{column:02d}"`.

### 3.2 `grid.xs` is one lattice per detected table

`grid.xs` is `TableGrid.xs` in `src/icpdf/parser/structure.py:68`, not a field of
`DetectedTable`:

```python
@dataclass
class TableGrid:
    bbox: BBox
    xs: list[float]
    ys: list[float]
    cells: list[GridCell] = field(default_factory=list)
    unassigned_words: list[TextWord] = field(default_factory=list)
    source: str = "rule_lattice"
```

`src/icpdf/parser/table_detector.py:127` builds exactly one grid per region:

```python
for region in detect_table_regions(layout, params):
    grid = recognize_structure(layout, region, params)
    ...
```

`recognize_structure()` (`structure.py:567`) delegates to `_rule_grid()` or
`_alignment_grid()`. `_rule_grid()` creates one `all_xs` at
`structure.py:454`:

```python
all_xs = _unique(edges + hard_xs + header_candidates + soft_xs, 4.0)
```

and one `TableGrid(bbox, all_xs, ys, cells, source=region.source)` at
`structure.py:500`. `_alignment_grid()` likewise creates one `xs` list
(`structure.py:536-538`). There is no per-row or per-component x lattice.

`GridCell` (`structure.py:57`) is:

```python
row, column, row_span, column_span, bbox, text="", word_count=0
```

It does not retain word ids. `_assign_words()` (`structure.py:313-332`) assigns
each `TextWord` by center to one cell and then discards the list after setting
`cell.text` and `cell.word_count`. S2b must therefore capture word ids in the
same pass or recompute the same deterministic assignment; §9 defines the rule.

### 3.3 `region_components` is provenance, not a second lattice

`src/icpdf/parser/table_regions.py` merges stacked components into one
`TableRegion`. `_merge_pair` requires shared column rules, a minimum shared
ratio, horizontal-extent alignment and no caption in the gap
(`TableParams.merge_*`). `_region_from_cluster()` then builds one region and
`_union_component()` unions the members' segments into one `RuleComponent`
(`table_regions.py:251-299`). `_region_from_cluster()` also emits structured
`RegionEvidence` with kinds `merge`, `absorbed` and `implied_outer`.

`DetectedTable.region_components` is filled at
`table_detector.py:176-177`:

```python
region_components=[component.component_id for component in region.components]
```

It records which components contributed to the one region that produced the
table. It does **not** select a per-region x lattice, and it cannot be used to
reinterpret `physical_column`.

`TableRegion` and `RegionEvidence` are at `structure.py:28-53`:

```python
@dataclass(frozen=True)
class RegionEvidence:
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
```

`DetectedTable` persists only `region_components`, `boundary_source` and
`merge_evidence` strings, not the structured `RegionEvidence`. S2b therefore
cannot recover an `implied_outer` extent from an old artifact; it must persist
the extent at derivation time (§5.3) or fail closed.

### 3.4 Header cells and role provenance

`HeaderCellRef` (`src/icpdf/parser/header_semantics.py:49`) is:

```python
level: int
column: int
text: str
bbox: BBox
source_row: int
source_column: int
```

The existing `Candidate` role fields (`src/icpdf/domain/candidate.py:62-67`)
are:

```python
column_role: ColumnRole = ColumnRole.UNKNOWN
role_source: str = "unknown"
role_header_cell_id: str | None = None
```

`build_candidates()` uses exactly three values for `role_source`
(`src/icpdf/parser/candidate_registry.py:64-69`):

```text
"header_text"   role equals the role derived from a printed header
"heuristic"     role came from a documented layout heuristic
"fail_closed"   no evidence; role is UNKNOWN
```

`ColumnRole` values are `min`, `typ`, `max`, `value`, `condition`, `unit`,
`symbol`, `unknown` (`src/icpdf/domain/candidate.py:13-21`).

### 3.5 Word ids

`TextWord.word_id` is deterministic
(`src/icpdf/parser/text_blocks.py:84`):

```python
f"p{page_number}-b{block_index}-l{line_index}-w{i}"
```

Spans use `...-s{span_index}` (`text_blocks.py:69`). Word ids are page-level and
stable for the same PDF, page and text extraction parameters. They are not
stored on `DetectedCell`; S2b must persist the ids it assigns.

### 3.6 Gold artifacts: versions, counts and logical fields (R2)

The repository contains two separately frozen Gold sets:

| Set | Manifest | `annotation_version` | Items | Tables | Negatives | Typed logical field |
| --- | --- | --- | --- | --- | --- | --- |
| Phase 1.2 | `gold/manifest.json` | `gold-2026-11-06.1` | 65 | 46 | 19 | no |
| Generalization v2 | `gold/generalization/manifest.json` | `gen-2026-11-06.2` | 29 | 21 | 8 | yes |

- `gold/versions/gold-2026-11-06.1/VERSION.json` fixes the v1 snapshot at source
  commit `b8c2d3bdf7b1b0900c6ad2204400b80a32dfdead`.
- `gold/generalization/versions/gen-2026-11-06.2/VERSION.json` fixes the v2
  snapshot at source commit `ee456ab2c6484649bddcac2a9217087c3a164190`.
- Both use `schema_version: gold-schema/v1`; the annotation version, not the
  schema version, distinguishes them.
- v1 tables have no `logical_columns`, `visual_columns`,
  `visual_boundary_status` or `partial_boundaries` keys at all.
- All 21 v2 tables have a non-null `logical_columns`, plus `visual_columns`,
  `visual_boundary_status` and `partial_boundaries`. No v2 table sets
  `logical_columns: null`.
- v2 table `column_boundaries` is documented as the logical column boundaries
  used for cells (`docs/GOLD_SPEC.md:48`); `visual_columns` is the count of
  printed visual intervals, `null` for `not_printed`.

**Why 67 and 65 are both correct:**

- `65` is the v1 item count: 46 tables + 19 negatives in one manifest.
- `67` is the count of positive tables across both sets: 46 + 21. The S2a
  physical-diff report uses "67 / 67 gold items" in this sense
  (`docs/PHASE1_4_S2A.md:570-572`). It is **not** a manifest item count and it
  excludes the 27 negatives (19 + 8).
- Only the 21 v2 tables carry typed logical annotations. The earlier sentence
  "Gold v2: 67 items, 21 with a decided logical mapping" conflated the 67
  positive tables with the 21 typed v2 tables. The correct statement is:
  "67 positive tables in the regression pool; 21 of them have typed logical
  columns; the 46 v1 tables are untyped for logical metrics."

The existing evaluator uses `gold_table.get("logical_columns", gold_columns)`
(`tools/goldset/evaluate.py:177`), so a v1 table falls back to its legacy
`n_columns`. That fallback is a compatibility behavior for historical reports.
It is **not** an annotation decision and S2b must not use it as one (§12.2).

### 3.7 Gold ambiguity is narrative, not a typed field

No Gold item has an `ambiguous` boolean or enum. In v1 the open ambiguities are
recorded in `review.independent_review_note`, for example:

- `ADS1299-P37-T01`: "Gold merges the partial Either-input band ... (open
  ambiguity 1)."
- `ADS1299-P70-T01`: "Gold keeps the partial band as a fifth column ... (open
  ambiguity 1)."
- `LM358-P04-T01`: "Gold encodes the partial Either-input band as two condition
  columns ... (open ambiguity 1)."
- `LM358-P04-T02`: headerless condition column; the parser's `UNKNOWN` is
  described as annotation debt, not a Gold error.
- `ADC12DJ5200-P46-T01`: leading `SYSREF` column role differs between Gold
  (`VALUE`) and the parser's leading-column heuristic (`SYMBOL`).

v2 (`gen-2026-11-06.2`) contains no "ambiguity" text in its item records. The
five examples above are v1 tables and are therefore also `untyped_legacy` for
logical metrics. §12.2 defines a read-only overlay that preserves their
identity without editing Gold.

## 4. Hard constraints

S2b must not:

- change `grid.xs`, `grid.ys`, physical cell bboxes/text, `column_index`,
  `row_span`, `column_span`, cell ids, Candidate ids or candidate identity;
- re-interpret or overwrite S2a `visual_*` fields;
- add a boundary because a target column count, a Gold value or a desired
  extraction result suggests one;
- use an LLM to propose, rank or select logical boundaries;
- change Gold v1/v2 or tune existing visual thresholds;
- create a second physical lattice, a per-region x renumbering, or a
  cross-table logical merge;
- treat a Gold `n_columns` fallback as a logical annotation;
- implement S2c (`ConditionContext` / `ConditionBand`), section-band semantics or
  Product Identity Resolution;
- push to Codeup.

S2b is an additive, derived annotation. The physical table remains the only
source of cells, text and candidates.

## 5. Data model (deliverable 1)

All proposed models are frozen Pydantic models. Parser-level models live beside
`DetectedTable`; domain models mirror the same fields in `domain/table.py`.
Field names below are proposals, not existing repository fields.

### 5.1 Enums

```text
LogicalMappingStatus = "resolved" | "unresolved"

LogicalBoundaryRole = "outer_left" | "outer_right" | "internal"

LogicalBoundarySource = "printed_rule" | "header_canopy" | "label_aligned"
                      | "structural" | "subrule_promoted"

LogicalBoundaryDecisionKind = "keep"
                            | "demote_no_evidence"
                            | "demote_condition_path"
                            | "unresolved"
```

`logical_mapping_status` is table-level. A legacy table or a table with no
decidable logical lattice is `unresolved`, not a third silent state.

The decision kind split is mandatory (P0-3): `demote_no_evidence` makes no
semantic claim; `demote_condition_path` is reserved for internal partial
sub-rules that meet the condition criteria in §6.5.

### 5.2 `LogicalBoundary` and `LogicalBoundaryDecision`

```text
LogicalBoundary
  x: float
  role: LogicalBoundaryRole
  sources: tuple[LogicalBoundarySource, ...]   # non-empty, sorted
  visual_boundary_index: int | None            # index into the parallel S2a tuples
  visual_coverage: float | None                # copied from S2a, never recomputed
  evidence: tuple[LogicalBoundaryEvidence, ...]  # non-empty
```

`DetectedTable.logical_boundaries` keeps the existing S2 interface type,
`tuple[float, ...]`, and holds the kept x positions in sorted order. The richer
records live in `logical_boundary_detail`, ordered identically; this avoids
changing the approved umbrella field type while keeping the evidence available.
Demoted and unresolved candidates are recorded separately in
`logical_boundary_decisions` so the decision remains auditable without
polluting the accepted lattice.

```text
BoundarySupport
  band_count: int
  rule_bands: int              # bands with a printed rule at x
  gutter_bands: int            # bands with a body gutter at x
  crossing_bands: int          # bands where a word run crosses x
  short_label_bands: int       # bands with a right-side short label
  condition_bands: int         # bands with condition-like right-side text
  nonempty_bands: int
  support_ratio: float         # rule/gutter support over non-empty bands
```

```text
LogicalBoundaryDecision
  candidate_x: float
  decision: LogicalBoundaryDecisionKind
  reasons: tuple[str, ...]                     # stable machine-readable codes
  sources: tuple[LogicalBoundarySource, ...]
  boundary: LogicalBoundary | None             # only when decision == "keep"
  demoted_to: "no_evidence" | "condition_path" | None
  support: BoundarySupport
  evidence: tuple[LogicalBoundaryEvidence, ...]  # all evidence seen at x
```

`demoted_to` is `None` for `keep` and `unresolved`. It is `"no_evidence"` for
`demote_no_evidence` and `"condition_path"` only for
`demote_condition_path`.

`logical_boundary_decisions` is a diagnostic record. It is retained even when
the table is `unresolved`, but it is never consumed by extraction and never
treated as a logical lattice.

### 5.3 Boundary evidence union (R4, P0-2)

`LogicalBoundaryEvidence` is a discriminated union, not one wide record with
optional fields. Each `kind` has its own required fields, and the validator can
reject a missing or mismatched reference without guessing which field was meant.

```text
PrintedRuleEvidence
  kind: "printed_rule"
  visual_boundary_index: int
  visual_segment_indices: tuple[int, ...]
  coverage: float

SubrulePromotedEvidence
  kind: "subrule_promoted"
  visual_boundary_index: int
  visual_segment_indices: tuple[int, ...]
  rule_bands: tuple[int, ...]
  short_label_bands: tuple[int, ...]
  short_label_word_ids: tuple[str, ...]
  nonempty_bands: int
  short_label_ratio: float

HeaderCanopyEvidence
  kind: "header_canopy"
  edge: "left" | "right" | "gap_left" | "gap_right"
  level: int
  header_cell_refs: tuple[HeaderCellRef, ...]
  left_label: str
  right_label: str

LabelAlignedEvidence
  kind: "label_aligned"
  grid_rows: tuple[int, ...]
  word_ids: tuple[str, ...]
  gutter_bands: int
  nonempty_bands: int
  gutter_ratio: float

StructuralEdgeEvidence
  kind: "structural"
  physical_cell_edge_refs: tuple[PhysicalCellEdgeRef, ...]
  physical_rule_component_ids: tuple[int, ...]

TableBBoxEvidence
  kind: "table_bbox"
  edge: "left" | "right"
  table_bbox: BBox

RegionExtentEvidence
  kind: "region_extent"
  edge: "left" | "right"
  region_component_ids: tuple[int, ...]
  extent_left: float
  extent_right: float
  boundary_source: str
```

`PhysicalCellEdgeRef`:

```text
grid_row: int
cell_index: int            # index inside DetectedRow.cells
edge: "left" | "right"
```

`HeaderCellRef` is the existing parser tuple
`(level, column, text, bbox, source_row, source_column)`; S2b does not create a
second header extraction.

Source-to-evidence mapping:

| `LogicalBoundarySource` | Required evidence kind(s) |
| --- | --- |
| `printed_rule` | `printed_rule` |
| `subrule_promoted` | `subrule_promoted` |
| `header_canopy` | `header_canopy` |
| `label_aligned` | `label_aligned` |
| `structural` | at least one of `structural`, `table_bbox`, `region_extent` |

Outer boundaries (`outer_left` / `outer_right`) additionally require
`table_bbox` evidence. When `boundary_source` is `implied_horizontal` or
`implied_alignment`, they also require `region_extent` evidence. A drawn outer
boundary may carry `printed_rule` as well, but `table_bbox` remains the
unconditional locator.

**Minimum evidence fields and rejection rules.** These are the validator rules
in §11, stated with their sources:

| Kind | Required references | Validation / rejection |
| --- | --- | --- |
| `printed_rule` | `visual_boundary_index`, non-empty `visual_segment_indices` | index in range; `abs(visual_boundaries[i] - x) <= visual_boundary_tol_pt`; each segment index in range; each `VisualSegment.component_id` in `region_components`; each `y0 < y1` inside table bbox; `coverage >= visual_full_height_coverage`; role must be `internal` for an internal boundary, `outer_*` for an outer one. Missing/invalid -> `boundary_evidence_missing_ref` or `boundary_evidence_mismatch`. |
| `subrule_promoted` | `visual_boundary_index`, non-empty `rule_bands`, `short_label_bands`, `short_label_word_ids` | same visual checks; coverage `< visual_full_height_coverage`; `rule_bands` inside grid rows; `short_label_bands` a subset of `rule_bands` with at least `logical_subrule_promote_min_bands`; `short_label_ratio >= logical_subrule_promote_min_ratio`; every word id exists, is right of `x`, and is in the same physical cell as its band. |
| `header_canopy` | non-empty `header_cell_refs`, `level`, `left_label`, `right_label` | at least one header cell on each side of `x` (or a gap between two cells); every ref resolves to a `DetectedHeaderCell` by `(level, source_row, source_column, column)`; `level < header_rows`; bbox inside the table; the referenced edge/gap is within tolerance of `x`; labels non-empty and distinct; the resulting interval is not empty. Missing cell -> `boundary_evidence_missing_ref`; unpaired sides -> `header_missing_for_canopy`. |
| `label_aligned` | non-empty `grid_rows`, non-empty `word_ids` | rows in `[header_rows, n_rows)`; every word id exists on the page and inside the table; no word crosses `x`; `gutter_ratio >= logical_label_min_band_ratio`; `len(grid_rows) >= logical_label_min_bands`. |
| `structural` | non-empty `physical_cell_edge_refs` | each ref resolves to a real `DetectedCell`; the referenced edge is within tolerance of `x`; the edge repeats in at least two distinct row bands; no word crosses `x`. `physical_rule_component_ids`, when present, must all be in `region_components`. |
| `table_bbox` | `edge`, `table_bbox` | only for outer boundaries; `x` equals `table_bbox[0]` (left) or `table_bbox[2]` (right) within tolerance. An internal boundary may not use this kind. |
| `region_extent` | `edge`, non-empty `region_component_ids`, `extent_left`, `extent_right`, `boundary_source` | only for outer boundaries; every component id in `region_components`; `boundary_source` in `{implied_horizontal, implied_alignment, mixed}`; `x` equals the relevant extent within tolerance; the extent values must match the `TableRegion.evidence[kind="implied_outer"].values` of a fresh parse. If the artifact has no structured extent, fail closed; do not infer it from the bbox alone. |

`visual_segment_indices` are indices into `VisualBoundary.segments` for the
boundary at `visual_boundary_index`. The S2a segment order is deterministic
(`visual_structure.py` sorts by `(x, y0, y1, component_id)`), so the same
parser and parameters reproduce the same indices. This is the only primitive
provenance chain; S2b does not copy `primitive_indices` a second time.

### 5.4 Projection models (R3, P1-2, P1-4)

```text
PhysicalColumnOverlap
  physical_column: int                 # 0-based interval index into the one grid.xs
  physical_left: float                 # grid.xs[physical_column]
  physical_right: float                # grid.xs[physical_column + 1]
  region_component_ids: tuple[int, ...]  # provenance only; may be empty
  grid_row_start: int                  # inclusive
  grid_row_end: int                    # inclusive
  overlap_left: float
  overlap_right: float
  overlap_fraction: float              # overlap width / physical column width

ColumnProjection
  logical_column: int
  left: float
  right: float
  physical_columns: tuple[PhysicalColumnOverlap, ...]  # non-empty
  visual_column_indices: tuple[int, ...]                # visual interval indices
```

`physical_column` is unique **within one table** because one table has exactly
one `grid.xs` (§3.2). `physical_left` / `physical_right` are copied from that
lattice at derivation time and are the self-checking locator; the validator
re-derives `grid.xs` from a fresh parse and requires
`physical_left == grid.xs[i]` and `physical_right == grid.xs[i + 1]`.
`grid_row_start` / `grid_row_end` are inclusive and inside
`[0, n_rows - 1]`.

`region_component_ids` records which components contributed the physical
column. It is provenance, not a lattice selector; there is no
`region_local_column` field because no region-local x lattice exists in the
current repository.

`visual_column_indices` are indices into the S2a **visual interval** grid
`0 .. visual_columns - 1`, not boundary indices. It is empty when the table's
`visual_columns` is `None` (`not_printed`). This resolves the old ambiguous
`visual_columns` field name: the table-level `visual_columns` remains the S2a
count; the projection field is named `visual_column_indices`.

`ColumnProjection` is the **only authoritative** projection payload. It lives
once on the table in `column_projection`, ordered by `logical_column`. A
proposed `LogicalColumn` does not embed a copy. The validator enforces
one-to-one order and interval equality between `column_projection[i]` and
`logical_columns_detail[i]`.

### 5.5 `LogicalColumn` and role provenance (P1-3)

```text
LogicalColumn
  logical_column: int
  header_path: tuple[str, ...]          # top-to-bottom, may be empty
  header_cell_refs: tuple[HeaderCellRef, ...]
  role: ColumnRole                      # existing vocabulary; "unknown" allowed
  role_source: "header_text" | "subrule_short_label"
             | "heuristic" | "fail_closed"
  role_evidence: str | None             # stable code, not prose
  role_header_cell_ref: HeaderCellRef | None   # parser level
  role_header_cell_id: str | None              # domain level
```

This aligns with the existing `Candidate` fields (§3.4) instead of inventing a
`header | unknown` vocabulary:

- header-derived role: `role_source = "header_text"`,
  `role_header_cell_ref` / `role_header_cell_id` populated;
- promoted sub-rule column: `role = condition`,
  `role_source = "subrule_short_label"` (the approved S2 value),
  `role_evidence = "repeated_short_label"`, header reference may be `None`;
- unlabelled column: `role = unknown`, `role_source = "fail_closed"`,
  `role_evidence = None`, no header reference;
- any other documented layout rule: `role_source = "heuristic"` with a stable
  `role_evidence` code naming the rule.

`role_source` is the existing free-form `str` on `Candidate`
(`domain/candidate.py:65`); `candidate_registry.py` currently emits
`header_text`, `heuristic` and `fail_closed`. The approved S2 design already
reserves `subrule_short_label` for a promoted sub-rule column, so S2b adopts it
as the fourth documented value rather than hiding it in a separate vocabulary.
`section_band` is not used in S2b; it belongs to S2c.

`role_header_cell_ref` and `role_header_cell_id` are the parser-level and
domain-level forms of the same link. The validator accepts at most one per
record and, when both are present, requires them to resolve to the same cell.
`role_evidence` is a stable code, not free prose.

### 5.6 Logical cells and word assignments (R7, P1-1)

```text
PhysicalCellRef
  grid_row: int          # DetectedRow.grid_row
  cell_index: int        # index inside DetectedRow.cells
  column_index: int      # DetectedCell.column_index, for readability
  cell_id: str | None    # domain id after rebuild; None at parser level

PhysicalCellAssignment
  ref: PhysicalCellRef
  word_ids: tuple[str, ...]   # subset of this physical cell's words

LogicalCell
  logical_cell_id: str                 # deterministic, content-independent
  row_start: int                       # inclusive physical grid row
  row_end: int                         # inclusive
  logical_column: int
  logical_column_span: int             # >= 1
  bbox: BBox
  text: str
  kind: "header" | "data"              # section/condition deferred to S2c
  physical_cells: tuple[PhysicalCellAssignment, ...]  # non-empty
  word_ids: tuple[str, ...]            # derived union; disjoint across cells
```

`PhysicalCellAssignment` is the missing piece in the previous design. A
physical cell is not owned wholesale by one logical cell: when a physical cell
straddles a promoted boundary, the same `PhysicalCellRef` appears in several
assignments, each with a disjoint word subset. `LogicalCell.text` is the
reading-order concatenation of its assigned words, not a copy of the physical
cell's full text. `LogicalCell.word_ids` is the union of its assignments; the
union across all logical cells is a disjoint partition.

`PhysicalCellRef.cell_index` is the parser-level identity because
`DetectedCell` has no `cell_id` (§3.1). After rebuild, `cell_id` is filled and
the domain `Cell` can use `cell_id` directly. `cell_index` is the index in
`DetectedRow.cells`, not the physical grid column; `column_index` is carried for
readability and must match the referenced cell.

The physical→logical cell relation is many-to-many and lives on the logical
side. A reverse cache `logical_cell_ids` on `DetectedCell` is derived, never
authoritative.

### 5.7 Additive table fields

`DetectedTable` / domain `Table` gain:

```text
logical_mapping_status: LogicalMappingStatus = "unresolved"
logical_mapping_reason: tuple[str, ...] = ()
logical_boundaries: tuple[float, ...] = ()               # accepted x positions
logical_boundary_detail: tuple[LogicalBoundary, ...] = ()  # parallel evidence
logical_columns: int | None = None
column_projection: tuple[ColumnProjection, ...] = ()
logical_columns_detail: tuple[LogicalColumn, ...] = ()
logical_cells: tuple[LogicalCell, ...] = ()
logical_boundary_decisions: tuple[LogicalBoundaryDecision, ...] = ()  # diagnostic
```

`logical_boundaries` and `logical_boundary_detail` are ordered identically:
`logical_boundaries[i] == logical_boundary_detail[i].x`. The simple x tuple is
the approved umbrella interface; the detail tuple carries evidence. The
validator enforces the parallel order and rejects a length mismatch.

`logical_boundary_decisions` is the only diagnostic payload retained on an
`unresolved` table; all accepted logical payloads stay empty (§10).

`DetectedCell` / domain `Cell` gain only derived caches:

```text
logical_cell_ids: tuple[str, ...] = ()
logical_columns: tuple[int, ...] = ()
word_ids: tuple[str, ...] = ()
```

Candidate identity is unchanged. Candidates may gain `logical_cell_refs` and
derived `logical_columns`; when the mapping is unresolved these are empty.

### 5.8 Parameters and snapshot compatibility (R6, P0-4)

All new thresholds are `TableParams` fields with **code defaults**, not YAML
entries. `configs/parser.yaml` is unchanged, so `parser_config_sha256` (the YAML
file hash) is unchanged for old and new runs. Proposed defaults, subject to
Reviewer approval:

| Parameter | Proposed default | Purpose |
| --- | --- | --- |
| `logical_label_min_band_ratio` | 0.60 | stable body-gutter support |
| `logical_label_min_bands` | 2 | minimum supporting row bands |
| `logical_subrule_promote_min_ratio` | 0.50 | short-label promotion |
| `logical_subrule_promote_min_bands` | 2 | minimum supporting bands |
| `logical_subrule_ambiguous_min_ratio` | 0.25 | lower bound of the ambiguous band |
| `logical_short_label_max_words` | 2 | short-label classification |
| `logical_short_label_max_chars` | 12 | short-label classification |

Boundary alignment uses the existing `visual_boundary_tol_pt` (2.5pt); no new
geometry tolerance is introduced.

**Current v1 snapshot.** `src/icpdf/parser/config.py:14` defines
`TABLE_PARAMS_SNAPSHOT_VERSION = "table-params/v1"`. The v1 snapshot is
`{"snapshot_version": "table-params/v1", "params": params.model_dump(mode="json")}`
(`config.py:70-75`), and `snapshot_sha256()` hashes canonical JSON with sorted
keys (`config.py:78-82`). The frozen v1 SHA is
`82d4df4d1cb3cac9741831b0db36e19fa80c1829abc18b3f8b1ab4ee1c6b9f0a`
(`docs/S2A_FREEZE.md`).

The v1 field set is exactly the 20 fields currently declared
(`config.py:23-49`):

```text
cell_gap_pt, row_gap_factor, column_tolerance, header_min_hits,
max_title_chars, max_cell_chars, min_numeric_cells, rule_min_width_pt,
rule_min_height_pt, alignment_min_rows, merge_min_gap_pt, merge_max_gap_pt,
merge_column_tol_pt, merge_min_shared_columns, merge_shared_ratio,
merge_extent_tol_pt, merge_min_x_overlap_ratio, visual_min_rule_span_pt,
visual_boundary_tol_pt, visual_full_height_coverage
```

**Version-dispatched serialization.** S2b must not change what a v1 snapshot
means. Proposed API:

```text
TABLE_PARAMS_SNAPSHOT_VERSION = "table-params/v2"
SUPPORTED_TABLE_PARAMS_SNAPSHOT_VERSIONS = ("table-params/v1", "table-params/v2")
V1_FIELDS = (the 20 names above)
V2_FIELDS = V1_FIELDS + (the seven logical_* names)

table_params_snapshot(params, *, version=TABLE_PARAMS_SNAPSHOT_VERSION) -> dict
    dump = params.model_dump(mode="json")
    fields = V1_FIELDS if version == "table-params/v1" else V2_FIELDS
    return {"snapshot_version": version,
            "params": {name: dump[name] for name in fields}}

table_params_sha256(params, *, version=...) -> str
    return snapshot_sha256(table_params_snapshot(params, version=version))
```

`snapshot_sha256()` itself is unchanged. It hashes the stored snapshot object,
not a freshly dumped model, so replaying an old artifact is stable without
knowing the current field set. The producer (`src/icpdf/parser/pipeline.py:38-39`
and `:118-119`) passes the current version explicitly; consumers
(`audit_visual_primitives.py:414`, `validate_evidence.py:316`) hash the stored
snapshot and never re-dump the model.

Compatibility rules:

1. New runs use `table-params/v2`; the snapshot contains exactly
   `V2_FIELDS` (the 20 v1 names plus the seven `logical_*` names).
2. A replayed `table-params/v1` snapshot contains exactly `V1_FIELDS` and
   re-hashes to `82d4df4d...`; no `logical_*` key is added during replay.
3. `run_config.json` and `run_manifest.json` store `snapshot_version`. Audit and
   validation read that stored version and dispatch; they never call
   `table_params_snapshot(params)` without it.
4. `TableParams(**stored_v1_params)` remains valid because the new fields have
   defaults, but the reconstructed object is never re-dumped as v1.
5. An unsupported or missing version is refused with
   `unsupported_table_params_snapshot_version`; it is not guessed as v1 or v2.
6. `configs/parser.yaml` is not edited. If the Reviewer later wants these
   defaults in YAML, that changes `parser_config_sha256` and requires a new run
   baseline; it is outside S2b.
7. `tools/audit_visual_primitives.py` still hashes the stored snapshot
   (`verify_identity`, `snapshot_sha256(snapshot)`), still checks
   `rule_primitives.py` and `GRID_TOL`, and still accepts
   `TableParams(**snapshot["params"])`. Adding fields to `config.py` does not
   change `rule_primitives.py`, so the S2a identity gate is unchanged.
8. `tools/validate_evidence.py` recomputes the hash from the stored snapshot
   (`validate_evidence.py:316-324`), so old runs keep passing. It also reads
   visual parameters from the stored `params`; new logical keys do not affect
   that path.

Required compatibility tests (S2b-Schema):

- replay a stored v1 snapshot and reproduce `82d4df4d...`;
- assert the v1 replay has no `logical_*` key;
- assert a v2 snapshot contains the seven new keys;
- run the S2a primitive audit on an old artifact and confirm zero identity
  errors;
- tamper the stored v1 snapshot and confirm the audit refuses;
- feed an unknown snapshot version and confirm refusal.

### 5.9 Interface comparison with `PHASE1_4_S2.md`

The umbrella design is the approved principle document, not a frozen schema.
This table makes every field-level difference explicit so the Reviewer can
accept or reject it before S2b-Schema.

| Umbrella `PHASE1_4_S2.md` | S2b proposal | Status |
| --- | --- | --- |
| `logical_boundaries: tuple[float, ...]` | unchanged, plus `logical_boundary_detail: tuple[LogicalBoundary, ...]` | type preserved; evidence is additive |
| `logical_columns: int \| None` | unchanged | aligned |
| `logical_mapping_status: str` | `"resolved" \| "unresolved"` | aligned |
| `column_projection` | `tuple[ColumnProjection, ...]`, authoritative | defined here |
| `logical_cells` | `tuple[LogicalCell, ...]`, with `PhysicalCellAssignment` | refined (R7) |
| `logical_headers`, `logical_header_path`, `logical_header_cells`, `logical_column_roles` | consolidated into `logical_columns_detail[i].header_path`, `.header_cell_refs`, `.role`, `.role_source`, `.role_header_cell_id` | **intentional consolidation**; avoids parallel arrays that can disagree (same failure class as P1-2) |
| `section_bands`, `condition_bands`, `condition_contexts` | absent | deferred to S2c |
| `DetectedCell.logical_cell_ids`, `.logical_columns`, `.word_ids` | unchanged derived caches | aligned |
| `Candidate.logical_cell_refs`, `.logical_columns` | unchanged additive fields | aligned |
| `TableParams.subrule_logical_span=0.85` | reuse existing `visual_full_height_coverage=0.85` | aligned by reuse |
| `TableParams.short_label_max_words`, `short_label_max_chars` | `logical_short_label_max_words`, `logical_short_label_max_chars` | renamed with `logical_` prefix |
| `TableParams.short_label_band_ratio=0.5` | `logical_subrule_promote_min_ratio=0.50` | renamed |
| `TableParams.crossing_epsilon_pt=0.5` | not introduced | S2c concern |
| `role_source` values | `header_text`, `subrule_short_label`, `heuristic`, `fail_closed`; `section_band` deferred | aligned with the existing field name and the approved promoted value |
| boundary sources | same five sources | aligned |

The only structural deviation is the consolidation of four per-column arrays
into one `logical_columns_detail` tuple. It is proposed because the arrays can
drift independently, exactly the problem P1-2 identified for `projection`.
Reviewer approval is requested for that consolidation in §14.

## 6. Candidate generation and decisions (deliverable 4)

### 6.1 Candidate set

Candidates are the union of:

1. internal positions of the frozen `grid.xs` (the recognition lattice);
2. S2a visual boundaries inside the table bbox;
3. header-canopy edges: left/right edges of `DetectedHeaderCell` bboxes that
   fall inside the table;
4. stable body gutters at x where no word crosses and at least
   `logical_label_min_bands` row bands have a gutter;
5. the two table bbox edges, always kept as `outer_left` / `outer_right`.

Candidates within `visual_boundary_tol_pt` are grouped into one candidate; the
group x is the mean, and every source and evidence record remains listed.
Candidates outside the table bbox or within tolerance of an outer edge are not
internal boundaries.

Outer boundaries are kept with `table_bbox` evidence. When
`boundary_source` is `implied_horizontal` / `implied_alignment`, they also carry
`region_extent` evidence; no vertical rule is fabricated.

No candidate is generated from a target count, a Gold value, a header label
alone or a cell's semantic content.

### 6.2 Decision table (R5)

For each grouped candidate, in deterministic x order:

| Evidence at x | Decision | Source |
| --- | --- | --- |
| within tolerance of an outer table edge | keep, `outer_*` | `structural` + `table_bbox` (+ `region_extent`) |
| S2a full-height printed rule (`coverage >= 0.85`) with no conflicting data-cell crossing | keep | `printed_rule` |
| partial rule, short labels on the right in `>= 50%` of non-empty bands and `>= 2` bands | keep | `subrule_promoted` |
| partial rule, short-label ratio in `[0.25, 0.50)` and `>= 2` bands | **unresolved** | — |
| partial rule, not promoted, and at least one band has condition-like right-side text | `demote_condition_path` | — |
| partial rule, not promoted, and no band has condition-like right-side text | `demote_no_evidence` | — |
| no rule, aligned with a distinct header-cell gap/edge at `>= 1` header level | keep | `header_canopy` |
| no rule, stable body gutter meeting the label thresholds and no crossing text | keep | `label_aligned` |
| no rule/header, candidate aligned with a repeated physical cell edge in `>= 2` row bands and no word crosses | keep | `structural` |
| none of the above: no allowed logical-boundary evidence at x | `demote_no_evidence` | — |
| a body data cell crosses x in every band where the candidate otherwise has support | **unresolved** | — |
| sources disagree on keep vs demote after grouping | **unresolved** | — |

A `colspan` body data cell is never evidence for a split. A crossing in a
header/section row does not veto a boundary supported in body rows. A full-height
printed rule inside a body merged cell is conflicting physical evidence, not
proof of a split.

### 6.3 Sub-rule promotion

The promotion test is the approved S2 rule:

1. for each row band the rule intersects, find the nearest word run immediately
   to the right inside the same physical cell;
2. classify it as a short label when it has at most 2 words and 12 characters,
   at least one letter, no digit, and is not a unit-only token;
3. promote when short labels occur in at least 50% of non-empty bands and in at
   least 2 bands;
4. ratio in `[0.25, 0.50)` with at least 2 bands is ambiguous, not a demotion.

Measured examples from the approved design:

- CY29FCT520 P06 `290.2` (coverage 0.576), right-side `Data` / `I` in 4 of 5
  bands -> promote, 6 -> 7 logical columns.
- CY29FCT520 P05 `193.9`, `266.0`, right side is condition prose -> demote to
  condition path.
- DS10CP152 P04 `346.1`, P05 `363.1`, right side is numeric/unit content ->
  demote with no semantic claim.

No threshold may be adjusted after seeing S2b results; changes require a new
design review.

### 6.4 Header-canopy boundaries

A header canopy can create a logical boundary with no printed rule. The
boundary is kept only when:

- at least one header level has a gap or cell edge at x within
  `visual_boundary_tol_pt`;
- the header cells on the two sides carry distinct labels (not two fragments of
  the same text run);
- the resulting interval contains at least one header cell or data cell; an
  entirely empty interval is not created by a header gap alone.

Example: CY29FCT520 P04 has four logical boundaries (362.9, 393.2, 452.6,
482.9) that exist only as header-canopy boundaries, giving 8 logical columns
against 4 visual columns. These x positions are added to the logical lattice
only; `grid.xs` is untouched.

### 6.5 Demotion semantics (R5, P0-3)

The previous design assigned `demoted_to = "condition_path"` to every demoted
candidate. That gave condition semantics to unrelated rejected boundaries. The
split is:

**`demote_no_evidence`** — no allowed evidence for a logical split.

- `demoted_to = "no_evidence"`, `reasons` includes `boundary_no_evidence`.
- Used for speculative `grid.xs` soft splits and for candidates with no
  rule/header/label/structural evidence.
- A non-promoted partial rule whose right side is numeric/unit content also
  lands here (for example DS10CP152 P04/P05). The `support` record still shows
  `rule_bands`; the name means "no evidence for a logical split and no S2c
  semantic claim", not "no printed rule".
- No S2c condition band is created.

**`demote_condition_path`** — an internal partial sub-rule with condition-like
right-side text.

- `demoted_to = "condition_path"`,
  `reasons = ("boundary_condition_subrule",)`.
- Preconditions: the candidate is internal; it has a partial printed rule
  (`0 < coverage < visual_full_height_coverage`); it was not promoted; the
  short-label ratio is below `logical_subrule_ambiguous_min_ratio` (otherwise the
  ambiguous branch already wins); at least one non-empty band has condition-like
  right-side text.
- "Condition-like" is deterministic: the right-side run contains at least one
  letter, is not a short label, is not unit-only, and is not purely numeric.
  This is the only content test in S2b; it does not read a cell's semantic
  category.
- `condition_path` is a **path label** for S2c. S2b emits no `ConditionBand`
  and no `ConditionContext`; it only preserves the demoted x, its row bands and
  its support for the later S2c stage.

A boundary that has both printed-rule evidence and no semantic claim remains
`demote_no_evidence`; a boundary that is condition-like but also ambiguous
(`[0.25, 0.50)`) remains `unresolved`, not `demote_condition_path`.

## 7. Physical→logical mapping (deliverable 2)

### 7.1 One physical lattice per table (R3, P0-1)

`PhysicalColumnOverlap.physical_column` is a 0-based interval index into the
**one** `grid.xs` of the table that produced the `DetectedTable` (§3.2). The
premise of the previous §6.2 — that regions may use different physical x
lattices — is not true in the current repository:

- `detect_tables()` maps one `TableRegion` to one `TableGrid` to one
  `DetectedTable`;
- `_region_from_cluster()` already merged stacked components into one region;
- `_rule_grid()` builds one `all_xs` and one `TableGrid`;
- `region_components` lists the merged components for provenance only.

Therefore `physical_column` is unique within the table, and
`region_component_ids` never selects a different lattice. `physical_left` /
`physical_right` are the self-checking locator, and the validator re-derives
`grid.xs` from a fresh parse.

**Out of scope:** aggregating separate `DetectedTable`s (for example a
cross-page continuation) into one logical table. If that is ever required, a new
design must introduce a table-level `physical_lattice_id` / lattice hash and a
region-local `(region_id, local_column_index, xs_left, xs_right)` tuple. S2b
does not do this, and no S2b field may be read as a region-local index.

### 7.2 Interval mapping

`ColumnProjection` is overlap-based, not a partition:

- one logical column may contain several physical columns (demoted sub-rules,
  wide condition columns);
- one physical column may be split into several logical columns (promoted
  sub-rules, header canopies);
- a logical column may span several physical columns across row bands within
  the same table.

For each logical column `[left, right]`, compute the overlap with every physical
column interval `[grid.xs[i], grid.xs[i + 1]]` that intersects it. Record only
positive overlaps. `overlap_fraction` is the overlap width divided by the
physical column width; it is informational and does not filter the mapping.

`physical_column` plus `physical_left` / `physical_right` is the locator.
`grid_row_start` / `grid_row_end` records the row band in which the overlap
applies. A logical column that spans several row bands may have several
overlaps with the same physical column, one per disjoint row band.

### 7.3 Cell projection and word assignment

For each physical row and logical column:

1. find physical cells whose bbox intersects the logical interval;
2. assign each `TextWord` by its center x to exactly one logical column; a word
   center exactly on a boundary goes left, deterministically, and the tie is
   recorded in the decision diagnostics;
3. if several physical cells fall in one logical column, emit one `LogicalCell`
   whose `physical_cells` lists all of them and whose text is their
   reading-order concatenation;
4. if a physical cell straddles a logical boundary, its words are partitioned
   across several `PhysicalCellAssignment`s that share the same
   `PhysicalCellRef`, but no word is duplicated;
5. `word_ids` across all logical cells form a disjoint partition of the words
   assigned to the table.

The per-cell assignment is the R7/P1-1 fix. A `LogicalCell` cannot be
reconstructed from `physical_cell_refs` plus a flat `word_ids` list, because
that does not say which words of a shared physical cell belong to which logical
cell. `PhysicalCellAssignment` does.

A physical cell may be referenced by several logical cells (header canopy,
section-like spanning cell, or word-level split). The reverse cache on the
physical cell lists all of them.

### 7.4 Mapping examples

- CY29FCT520 P04: visual column 1 contains logical MIN/NOM/MAX; one physical
  column maps to three logical columns.
- CY29FCT520 P05: visual columns 1–3 form one condition logical column; three
  physical columns map to one logical column.
- MICRF103 P03: six visual columns and six logical columns; the outer edges are
  implied, not printed, and the mapping must not invent a seventh column.

## 8. Merged cells and multi-level headers (deliverable 3)

### 8.1 `colspan`

`column_span` is a physical fact and never creates or removes a logical
boundary by itself.

- A header cell with `column_span > 1` is a canopy cover. It backs every logical
  column it covers; the same `HeaderCellRef` appears in each covered logical
  column's `header_cell_refs`, so the cover relation stays visible without a
  separate flag.
- A body data cell with `column_span > 1` that crosses a candidate boundary is
  treated band by band: that band does not support the boundary. If every
  supporting band is crossed and the candidate has no independent printed
  full-height rule or distinct header-canopy gap, the candidate is unresolved.
  A printed full-height rule inside a merged data cell is treated as conflicting
  physical evidence, not as automatic proof of a split.
- A merged cell that spans an entire row band (section/label row) is retained as
  a physical cell and projected to the logical cells it overlaps; a crossing in
  a header/section row does not veto a boundary supported in body rows. S2b does
  not assign section semantics; that is deferred to S2c.

### 8.2 Multi-level headers

- Header levels are read from the existing `DetectedHeaderCell.level`.
- For each logical column and each level, select header cells whose bbox overlap
  with the logical interval is positive; the cell with the largest overlap wins.
  A tie at the same level is ambiguous.
- `header_path` is the top-to-bottom list of winning labels. Missing levels are
  skipped, not filled from neighbours; `header_cell_refs` records exactly which
  printed cells supplied each label.
- A canopy cell may appear at the same level for several logical columns; that
  is intentional and is not a duplicate-header error.
- Header text is never split or rewritten. Logical header attribution only
  references existing printed cells.

### 8.3 Blank and headerless areas

- A fully ruled, entirely blank physical column stays in the logical lattice
  with `role = "unknown"`; its boundaries are kept as `printed_rule` because the
  full-height printed rules are the evidence.
- A wide blank gutter with no rule, no header and no stable body gutter is not
  a candidate and cannot create a logical column. If such an x came from a
  speculative `grid.xs` soft split, it is `demote_no_evidence`; a full-height
  printed rule is handled by the first bullet, not by this one.
- A table with no header at all may still have a decided logical lattice from
  printed rules and body gutters; header paths are empty and are not a failure.

## 9. Evidence chain (deliverable 5, R7)

### 9.1 Walkable chain

Every accepted logical fact must be walkable back to the source:

```text
LogicalBoundary
  -> LogicalBoundaryEvidence (discriminated union)
     -> S2a VisualBoundary / VisualSegment (by index)
        -> VisualSegment.primitive_indices (page-level collect_primitives)
     -> DetectedHeaderCell (level, source_row, source_column, bbox)
     -> grid rows and TextWord.word_id
LogicalColumn
  -> ColumnProjection -> PhysicalColumnOverlap
     -> physical_column + physical_left/right (the table's one grid.xs)
     -> region_component_ids (provenance)
  -> HeaderCellRef -> DetectedHeaderCell
LogicalCell
  -> PhysicalCellAssignment -> PhysicalCellRef
     -> DetectedRow.grid_row + index in DetectedRow.cells
     -> domain cell_id after rebuild
  -> word_ids -> TextWord.word_id (deterministic page-level id)
     -> TextWord.bbox and block/line indices
```

No logical record may carry an x, label or text that is not backed by one of
these references. `LogicalBoundaryEvidence.visual_segment_indices` uses the S2a
record by index rather than copying primitive indices, so there is one primitive
provenance chain, not two.

### 9.2 Reference resolution rules

The read-only audit re-resolves every reference against a fresh parse:

- `visual_boundary_index`: in range of `visual_boundaries` /
  `visual_boundary_evidence`; the x at that index is within
  `visual_boundary_tol_pt` of the logical boundary; the role matches the S2a
  boundary role and the logical role.
- `visual_segment_indices`: in range of the referenced `VisualBoundary.segments`;
  each segment resolves to a `VisualSegment` with the same `component_id`,
  `y0`, `y1`; the component id is in `region_components`; the segment span is
  inside the table bbox.
- `header_cell_refs`: resolve by `(level, source_row, source_column, column)`
  to exactly one `DetectedHeaderCell`; text and bbox must match; `level <
  header_rows`; the cell belongs to this table.
- `grid_rows`: in `[header_rows, n_rows)`; each row is a real band; no row is
  repeated.
- `word_ids`: each id exists exactly once on the page; its center is inside the
  referenced physical cell bbox (same 0.8pt tolerance as `_assign_words`) and
  inside the logical cell bbox. Across every `PhysicalCellAssignment` of the
  table a word id appears at most once. If one physical cell is referenced by
  more than one logical cell, those assignments must carry disjoint `word_ids`
  sets; the union over the table is a disjoint partition of the table's
  assigned words.
- `physical_cell_edge_refs`: `(grid_row, cell_index)` resolves to a real
  `DetectedCell`; `column_index` matches; the edge x is within tolerance of the
  logical boundary.
- `physical_column`, `physical_left`, `physical_right`: `physical_column` is a
  valid interval index; `physical_left == grid.xs[i]` and `physical_right ==
  grid.xs[i + 1]`; no duplicate interval index in one logical column with the
  same row band.
- `region_component_ids`: every id is in `region_components`; for
  `region_extent`, the extent values match the fresh `TableRegion` evidence.

### 9.3 Independent reconstruction of a logical cell

Given a persisted `LogicalCell`, an independent reader can rebuild it without
running the S2b decision logic:

1. take `physical_cells`; for each `PhysicalCellAssignment`, resolve
   `PhysicalCellRef` to a physical cell and take exactly the listed `word_ids`;
2. resolve each word id to its `TextWord` (page, block, line, bbox) and check it
   lies inside both the physical cell and the logical cell bbox;
3. concatenate the assigned words in reading order; the result must equal
   `LogicalCell.text`;
4. take the union of all assignment word ids; it must equal
   `LogicalCell.word_ids`;
5. across all logical cells of the table, the assignment word ids must be
   pairwise disjoint and must cover exactly the words assigned to the table
   (excluding `unassigned_words`);
6. the same physical cell may appear in several assignments, but the word
   subsets must be disjoint. This is the check that a shared physical cell was
   split, not duplicated.

This is the independently reconstructable chain the Reviewer requested: the
evidence is per physical cell, per word, and it does not depend on the order in
which the algorithm emitted logical cells.

## 10. Failure strategy (deliverable 6)

### 10.1 Table-level fail-closed

If any candidate is `unresolved`, or any mapping invariant fails:

```text
logical_mapping_status = "unresolved"
logical_mapping_reason = (stable reason codes)
logical_columns = None
logical_boundaries = ()
logical_boundary_detail = ()
column_projection = ()
logical_columns_detail = ()
logical_cells = ()
```

`logical_boundary_decisions` remains available for diagnosis, but it is marked
non-authoritative and is not consumed by extraction. The physical table, S2a
visual fields and candidates remain exactly as before.

### 10.2 Reason codes

Proposed stable codes:

```text
boundary_ambiguous_subrule_ratio
boundary_conflicting_sources
boundary_data_cell_crossing
boundary_header_gap_too_wide
boundary_no_evidence
boundary_condition_subrule
boundary_partial_rule_not_condition
boundary_evidence_missing_ref
boundary_evidence_mismatch
boundary_evidence_stale
mapping_physical_overlap_missing
mapping_lattice_index_mismatch
mapping_word_not_assigned
mapping_word_partition_mismatch
header_level_tie
header_missing_for_canopy
header_role_source_invalid
region_lattice_inconsistent
unsupported_table_params_snapshot_version
```

A table may carry several codes. Codes are evidence for review, not an
alternative decision mechanism.

### 10.3 No guessing

- Never choose the interpretation that yields a target column count.
- Never choose the interpretation that improves a metric or matches Gold.
- Never fill a missing header from a neighbour.
- Never create a logical column from an empty interval.
- Never downgrade an ambiguity to a demotion to keep the table `resolved`.
- Never treat a Gold `n_columns` fallback as a logical annotation.
- Never infer a `region_extent` from the bbox when the structured extent is
  absent; fail closed instead.

## 11. Invariants and validator checks

Proposed invariants, checked by a new read-only validator (not the S2a
validator):

1. `logical_columns is null` iff `logical_mapping_status == "unresolved"`;
   unresolved tables carry no accepted logical payload.
2. `logical_boundaries` and `logical_boundary_detail` have equal length,
   `logical_boundaries[i] == logical_boundary_detail[i].x`, the x tuple is
   sorted and unique, every x is inside the table bbox, and every internal
   boundary has at least one allowed source.
3. `logical_columns == len(logical_boundaries) - 1` when resolved.
4. `column_projection` is the authoritative projection: length equals
   `logical_columns`, order matches `logical_columns_detail`, and each
   `ColumnProjection` has a non-empty `physical_columns`.
5. Every `PhysicalColumnOverlap.physical_column` is a valid index into the
   table's one `grid.xs`; `physical_left == grid.xs[i]`,
   `physical_right == grid.xs[i + 1]`; the overlap is positive; the row band is
   inside `[0, n_rows - 1]`.
6. Every logical column overlaps at least one physical column and every
   physical column overlaps at least one logical column.
7. On a resolved table, every `visual_column_indices` entry is in
   `[0, visual_columns - 1]` and has positive overlap; the tuple is empty iff
   the table's `visual_columns` is `None`.
8. Every kept boundary's evidence resolves per §5.3/§9.2; a missing reference is
   an error, not a warning. A source whose evidence kind does not match its
   declared source is an error.
9. `LogicalCell.physical_cells` is non-empty; every `PhysicalCellRef` resolves;
   the assignment word ids are pairwise disjoint and their union equals
   `LogicalCell.word_ids`; across the table the union is a disjoint partition of
   the table's words.
10. `LogicalCell.text` equals the reading-order concatenation of its assigned
    words; it is not an unmodified copy of a shared physical cell.
11. Header references exist, belong to the table, and their levels are within
    `header_rows`; `role_source` is one of `header_text`,
    `subrule_short_label`, `heuristic`, `fail_closed`; `role_header_cell_id`
    resolves when present; `subrule_short_label` requires `role = condition`
    and short-label evidence.
12. Physical and S2a fields are unchanged: `grid.xs`, `grid.ys`, cell bboxes,
    cell text, `column_index`, `row_span`, `column_span`, `visual_boundaries`,
    `visual_boundary_status`, `visual_columns`, `partial_boundaries`,
    `visual_boundary_evidence`.
13. Candidate ids and counts are unchanged; candidate logical refs are empty on
    unresolved tables.
14. Old run artifacts without logical fields still load and are treated as
    `unresolved`, not as a parse failure.
15. A replayed `table-params/v1` snapshot reproduces the frozen v1 SHA and
    contains no `logical_*` key; a v2 snapshot contains exactly `V2_FIELDS`
    (the 20 v1 names plus the seven `logical_*` names).

## 12. Evaluation set and metrics

### 12.1 Sets and exact counts (R2)

**A. Regression set (must not change).**

- Gold v1: `gold/gold_table_set.jsonl`, `annotation_version
  gold-2026-11-06.1`: 46 tables + 19 negatives = 65 items.
- Gold v2: `gold/generalization/gold_table_set.jsonl`,
  `annotation_version gen-2026-11-06.2`: 21 tables + 8 negatives = 29 items.
- Combined positive pool: 67 tables (46 + 21); combined negatives: 27 (19 + 8).
- Phase 1.3 and 1.4 samples, including the six S2a PDFs.
- Checks: S1 physical fields and S2a visual fields zero-diff; candidate ids and
  counts zero-diff; old artifacts load as `unresolved`.

**B. Logical-structure set (new, separately frozen).**

This set is the only source of physical→logical projection and word-partition
ground truth. Gold v2 supplies counts, logical `column_boundaries`, headers and
roles, but it does **not** contain a typed physical→logical projection or a
word partition. The mapping-exact and LogicalCell-exact metrics are therefore
evaluated only on this set, not on Gold v2.

Cases required, each with its own annotation and source PDF SHA:

- cross-column canopy header;
- multi-level header with merged levels;
- merged data cell (`colspan` / `rowspan`);
- blank separator column;
- several physical columns forming one logical field;
- one physical cell referenced by several logical semantics;
- stacked components sharing one logical column inside one region;
- a split physical cell with a per-word assignment.

Known v2 examples can seed this set (CY29FCT520 P04/P05/P06/P08, MICRF103 P03,
DS10CP152 P04/P05/P11), but the set is stored under `gold/s2b/` with its own
manifest, `annotation_version`, `VERSION.json` and SHA. Gold v2 is never edited.

**C. Negative set.**

- boundary with no evidence;
- sub-rule ratio in the ambiguous band;
- missing `HeaderCell` for a canopy boundary;
- physical evidence conflict (data cell crossing a candidate);
- two equally valid logical interpretations;
- incomplete cross-page evidence;
- legacy artifact with no logical fields.

The negative set asserts `logical_mapping_status == "unresolved"` and that
physical/S2a/candidate fields are untouched. It must not assert a made-up
logical count.

### 12.2 Gold logical status and ambiguity overlay (P1-5)

Gold ambiguity and algorithm uncertainty are two different axes and must be
stored and evaluated separately.

**Algorithm axis (on the predicted table):**

```text
logical_mapping_status = "resolved" | "unresolved"
```

**Gold/evaluation axis (on the evaluation manifest, not on the Gold file):**

```text
gold_logical_status = "decided" | "ambiguous" | "undecided" | "untyped_legacy"
```

- `decided`: the table has a non-null typed `logical_columns` and no open
  ambiguity overlay. Only these tables enter the logical exact-match,
  mapping-exact and header/role denominators.
- `ambiguous`: an open ambiguity overlay entry exists. The table is reported in
  the ambiguity bucket and is excluded from the decided denominators. It is not
  an algorithm failure by itself.
- `undecided`: the table explicitly records `logical_columns: null`; excluded
  from the decided denominators and reported as `logical_column_excluded_undecided`.
- `untyped_legacy`: the table has no typed logical field (all v1 tables). It is
  excluded from logical metrics; it remains in detection, row, cell-text and
  visual metrics. The evaluator must not use the
  `gold_table.get("logical_columns", gold_columns)` fallback for S2b logical
  metrics.

Precedence is fixed and checked by the evaluator: an overlay entry makes a
table `ambiguous` even when it is also v1 and therefore `untyped_legacy` for
logical exactness. Such a table stays excluded from the logical exact-match
denominator (it has no typed logical annotation) but still counts in ambiguity
detection. `decided` is assignable only to a table with typed logical fields
and no overlay entry; `undecided` requires an explicit typed `null`.

**Ambiguity overlay.** The five named v1 cases are preserved without editing
Gold:

```text
gold/s2b/ambiguity_manifest.json
  schema_version: "s2b-ambiguity/v1"
  gold_set: "gold-2026-11-06.1"
  annotation_version: "gold-2026-11-06.1"
  items:
    - ambiguity_id: "AMB-COND-BAND-MERGED-01"
      item_id: "ADS1299-P37-T01"
      kind: "merged_vs_split_condition_band"
      status: "open"
      competing_interpretations: ["merged", "split"]
      gold_note_ref: "review.independent_review_note"
      evidence: "gold/overlays/ADS1299-P37-T01.png"
      note: "Gold merges the partial Either-input band while two sibling items split it."
    - ambiguity_id: "AMB-COND-BAND-SPLIT-01"
      item_id: "ADS1299-P70-T01"
      kind: "merged_vs_split_condition_band"
      status: "open"
      competing_interpretations: ["merged", "split"]
      gold_note_ref: "review.independent_review_note"
      evidence: "gold/overlays/ADS1299-P70-T01.png"
      note: "Gold keeps the partial band as a fifth column (split near x=112); frozen for comparability."
    - ambiguity_id: "AMB-COND-BAND-SPLIT-02"
      item_id: "LM358-P04-T01"
      kind: "merged_vs_split_condition_band"
      status: "open"
      competing_interpretations: ["merged", "split"]
      gold_note_ref: "review.independent_review_note"
      evidence: "gold/overlays/LM358-P04-T01.png"
      note: "Gold encodes the partial Either-input band as two condition columns (6); the parser reports 5."
    - ambiguity_id: "AMB-ROLE-UNKNOWN-01"
      item_id: "LM358-P04-T02"
      kind: "headerless_condition_role"
      status: "open"
      competing_interpretations: ["condition", "unknown"]
      gold_note_ref: "review.independent_review_note"
      evidence: "gold/overlays/LM358-P04-T02.png"
      note: "role unknown is correct; do not invent a label"
    - ambiguity_id: "AMB-ROLE-LEADING-01"
      item_id: "ADC12DJ5200-P46-T01"
      kind: "leading_column_role"
      status: "open"
      competing_interpretations: ["value", "symbol"]
      gold_note_ref: "review.independent_review_note"
      evidence: "gold/overlays/ADC12DJ5200-P46-T01.png"
      note: "Gold calls the leading SYSREF bit-field column VALUE; the leading-column heuristic calls it SYMBOL."
```

The overlay validator (read-only) checks that every `item_id` exists in the
declared `gold_set`, that `gold_note_ref` resolves to a non-empty string in the
Gold item, that the referenced `evidence` file exists, and that the same
`item_id` never appears in two entries.

Rules:

- The overlay is read-only with respect to Gold. It records identity, the
  competing interpretations and the existing review note; it never rewrites a
  Gold value.
- No algorithm output may create, resolve or influence an overlay entry.
- An `ambiguous` item is excluded from the decided denominator and reported
  separately; it is never counted as a resolved exact match.
- `LM358-P04-T02` is retained as the case where `role = unknown` is correct;
  the design must not "fix" it by inventing a label.
- An ambiguous item may be included in the negative/ambiguous detection set.
  The only assertion there is `logical_mapping_status == "unresolved"`; the
  evaluation never requires the algorithm to pick one of the competing Gold
  interpretations, and never asserts a made-up logical column count.
- The overlay is frozen with the S2b set; later additions require a new
  `s2b` evaluation version.

### 12.3 Metrics

| Metric | Definition | Denominator |
| --- | --- | --- |
| LogicalBoundary precision / recall | matched kept boundaries within 2.5pt vs Gold logical `column_boundaries` | predicted / Gold boundaries on `decided` tables with typed boundaries |
| LogicalColumn exact match | predicted count and ordered intervals equal Gold `column_boundaries` | `gold_logical_status == "decided"` |
| Physical→logical mapping exact match | each logical column's physical column set, `physical_left/right` and row-band overlaps equal the S2b-set annotation | S2b-set cases with an annotated projection |
| LogicalCell projection exact match | row range, logical column span, physical cell set and per-cell word partition equal the S2b-set annotation | S2b-set annotated projection cases |
| Header provenance coverage | logical columns with a complete, existing header cell chain | labelled logical columns on `decided` tables |
| Ambiguous detection recall | gold-ambiguous cases predicted `unresolved` | gold-ambiguous cases (reported separately) |
| Zero-regression | S1/S2a/candidate fields byte-identical | all regression tables |

Report per-item results and a failure list; never report only a single exact
match. A boundary count match with a wrong physical mapping is a failure, not a
pass. A Gold-ambiguous case is never counted as a resolved exact match.

### 12.4 Anti-overfitting rules

- Freeze the S2b evaluation manifest and SHAs before the first prototype run.
- Fix the proposed parameters before seeing results; any change requires a new
  design review and a new evaluation version.
- Do not add a table to the set because it fixes a metric; do not remove a
  failing table.
- Do not use Gold logical counts as an input to the algorithm, directly or
  indirectly.
- Do not use algorithm output to resolve or modify a Gold ambiguity overlay.

## 13. Staged delivery and review gates

| Stage | Deliverable | Allowed changes | Gate |
| --- | --- | --- | --- |
| S2b-Design | this document | docs only | Reviewer approval required |
| S2b-Schema | models, additive fields, read-only validator, unit tests | no detector integration; no S1/S2a/Gold change | Reviewer checks schema, evidence union and snapshot compatibility |
| S2b-Prototype | logical lattice on the standalone S2b set | no pipeline integration; no extraction dependencies | Reviewer checks boundaries, mapping, word partition and failure behavior |
| S2b-Integration | detector/rebuilder integration, full regression, compatibility report | additive wiring only; no physical or S2a change | Reviewer checks zero regression and evidence completeness |

No stage may begin before the previous gate is approved. S2b-Integration is not
authorized by S2a freeze or by this design.

## 14. Open decisions for Reviewer

1. Approve the proposed logical parameters and the version-dispatched
   `table-params/v2` snapshot, including the frozen v1 field list and the
   replay rules in §5.8.
2. Approve retaining `logical_boundary_decisions` as a non-authoritative
   diagnostic on unresolved tables (accepted payload remains empty).
3. Confirm that a fully ruled blank column is kept as a `printed_rule` logical
   column with `role = "unknown"`, rather than treated as an unresolved case.
4. Confirm that section-band semantics and condition bands remain out of S2b;
   `demote_condition_path` is only a path label for S2c and emits no band.
5. Confirm that header-canopy boundaries may add logical x positions where
   `grid.xs` has no boundary, as long as the physical grid is untouched.
6. Confirm the location/name of the new S2b evaluation set (`gold/s2b/`), its
   ambiguity overlay, and its freeze procedure.
7. Confirm the role provenance alignment: `role_source` uses the existing
   `header_text` / `heuristic` / `fail_closed` values plus the approved S2
   `subrule_short_label`, `role_evidence` carries a stable code, and
   `role_header_cell_id` carries the domain `HeaderCell.header_cell_id`.
8. Confirm that all v1 tables are `untyped_legacy` for logical metrics and that
   the existing `n_columns` fallback is not used as a logical annotation.
9. Confirm that `PhysicalColumnOverlap` is table-global (one `grid.xs` per
   table) and that cross-table aggregation is out of scope for S2b.

## 15. Acceptance checklist for the design gate

- [ ] Six deliverables are answered: data model, mapping, merged cells,
      boundary decisions, evidence chain, failure strategy.
- [ ] R1–R7 are answered with repository paths and line references.
- [ ] P0-1..P0-4 and P1-1..P1-5 are closed in the document.
- [ ] Hard constraints in §4 are accepted.
- [ ] Proposed parameters and the v1/v2 snapshot dispatch are approved or
      amended.
- [ ] S2b evaluation set, ambiguity overlay, metrics and anti-overfitting rules
      are approved.
- [ ] No implementation is authorized until this design gate passes.
