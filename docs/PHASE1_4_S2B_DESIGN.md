# Phase 1.4 S2b — Logical Boundary Lattice and Projection

**Status:** design proposal only (revision r3, based on `eac55f4`). No
implementation, schema change, Gold change or pipeline integration is authorized
by this document. Implementation starts only after the Reviewer closes the
items in §1.

**Relationship to the approved S2 design:** `docs/PHASE1_4_S2.md` remains the
umbrella design. S2b narrows its §5–§7 to the logical column lattice and the
physical→logical projection. Where this document is more specific, it is a
proposal for review, not a replacement of the approved principles.

## 1. Review resolution map

This revision answers the seven review items and the P0/P1 findings on
`cf59799` (r2), plus the eight blocking findings in the r2 re-review. Nothing
below is an implementation claim; every repository statement is backed by a
path and line reference in §3.

**r3 review findings (latest round).**

| Item | Reviewer finding | Answer in |
| --- | --- | --- |
| N1 | `HeaderCanopyEvidence` has an undirected ref set; the auditor must re-run the left/right decision | §5.3, §9.2, §11 |
| N2 | `SubrulePromotedEvidence` lacks per-band, per-cell word attribution; ratio is not independently recomputable | §5.3, §6.3, §11 |
| N3 | `TableBBoxEvidence` / `RegionExtentEvidence` are only self-consistent, not anchored to a fresh parse | §5.3, §9.2, §11 |
| N4 | Candidate grouping can chain-merge beyond tolerance; no fixed anchor | §6.1, §11 |
| N5 | `condition_path` lexical rule is too broad; ratio definition incomplete | §6.5, §6.3 |
| N6 | `LogicalCell` bbox, id, rowspan/colspan and word-universe reconstruction rules are incomplete | §5.6, §7.3, §9.3, §11 |
| N7 | Gold annotation type and ambiguity overlay are still collapsed into one status | §12.2 |
| N8 | v1/v2 snapshot validation is hash-only; S2a audit edit boundary is undefined | §5.8, §13 |
| S1 | §5.5 "at most one ref" contradicts "both present must agree" | §5.5 |
| S2 | Projection row bands, visual intervals and overlap recomputation are under-specified | §5.4, §7.2, §11 |
| S3 | Structural edge de-duplication, header overlap formula, boundary tie-break, cell kind edge cases | §5.3, §7.3, §8.2, §11 |

**r2 findings (kept for traceability).**

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
  band_count: int              # canonical body bands the candidate intersects
  rule_bands: int              # bands with a printed rule at x
  gutter_bands: int            # bands with a body gutter at x
  supported_bands: int         # union of rule/gutter bands, each counted once
  crossing_bands: int          # bands where a word run crosses x
  short_label_bands: int       # bands with a right-side short label
  condition_bands: int         # bands with condition-like right-side text
  nonempty_bands: int          # evidence-specific denominator, see below
  support_ratio: float         # supported_bands / nonempty_bands
```

`support_ratio` is diagnostic only and never decides a boundary by itself; the
decision uses the named thresholds in §6.2. A band that has both a rule and a
gutter increments `rule_bands` and `gutter_bands` individually but only once in
`supported_bands`, so the ratio is `<= 1.0` by construction. `band_count` and
`nonempty_bands` are computed over the canonical bands of §5.4 (body bands for
`label_aligned`); a candidate that intersects no band has
`nonempty_bands == 0` and no ratio. The denominator is:

- `subrule_promoted`: bands with at least one word center strictly right of x;
- `label_aligned`: body bands with at least one word anywhere in the table;
- other kinds: bands with at least one word anywhere in the table.

Both denominators are restated on the corresponding evidence record, so the
validator never has to infer which one a decision used.

```text
LogicalBoundaryDecision
  candidate_x: float                           # group x
  anchor_x: float                              # fixed anchor of the group
  source_xs: tuple[float, ...]                 # every member x, sorted, unique
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

SubruleLabelAssignment
  grid_row: int
  physical_cell_ref: PhysicalCellRef
  word_ids: tuple[str, ...]          # non-empty, reading order
  selected_run_bbox: BBox            # union of the assigned word bboxes
  classification: "short_label"

SubrulePromotedEvidence
  kind: "subrule_promoted"
  visual_boundary_index: int
  visual_segment_indices: tuple[int, ...]
  rule_bands: tuple[int, ...]        # sorted, unique
  nonempty_bands: int
  label_assignments: tuple[SubruleLabelAssignment, ...]  # one per band at most
  short_label_ratio: float

HeaderCanopyEvidence
  kind: "header_canopy"
  level: int
  boundary_edge: "left" | "right" | "gap"
  left_header_cell_refs: tuple[HeaderCellRef, ...]
  right_header_cell_refs: tuple[HeaderCellRef, ...]
  left_anchor_ref: HeaderCellRef
  right_anchor_ref: HeaderCellRef
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
  physical_cell_edge_refs: tuple[PhysicalCellEdgeRef, ...]  # sorted, unique
  physical_rule_component_ids: tuple[int, ...]

TableBBoxEvidence
  kind: "table_bbox"
  edge: "left" | "right"
  page_number: int
  table_bbox: BBox

RegionExtentEvidence
  kind: "region_extent"
  edge: "left" | "right"
  page_number: int
  region_component_ids: tuple[int, ...]
  extent_left: float
  extent_right: float
  boundary_source: str
  implied_outer_evidence_index: int
  implied_outer_values: tuple[float, ...]
```

**`HeaderCanopyEvidence` is directed (N1).** The record is self-explanatory:
the audit does not re-run the canopy decision.

- `boundary_edge` defines x from the anchors:
  - `left`: x equals `right_anchor_ref.bbox[0]` (within
    `visual_boundary_tol_pt`);
  - `right`: x equals `left_anchor_ref.bbox[2]`;
  - `gap`: x equals
    `(left_anchor_ref.bbox[2] + right_anchor_ref.bbox[0]) / 2`; the gap width
    must be positive and no header cell at that level may intersect the open
    gap.
- `left_anchor_ref` must appear in `left_header_cell_refs` and
  `right_anchor_ref` in `right_header_cell_refs`. Anchors are the cells
  immediately adjacent to x at `level`.
- `left_header_cell_refs` lists every header cell at `level` whose x-span lies
  wholly on the left (`bbox[2] <= x + tol`), nearest first; the right list is
  the mirror image (`bbox[0] >= x - tol`, nearest first). Extra refs are
  provenance for a multi-cell canopy, not additional anchors.
- `left_label` / `right_label` are the normalized texts of the anchors
  (strip, collapse internal whitespace); both non-empty and distinct.
- If two cells at the same level touch x within tolerance, the candidate is
  `unresolved` (`header_level_tie`); one anchor per side is mandatory.
- Every ref has `level == evidence.level` and resolves to exactly one
  `DetectedHeaderCell` by `(level, source_row, source_column, column)`; its bbox
  is inside the table bbox.

**`SubrulePromotedEvidence` is per band, per cell, per word (N2).**

- `rule_bands` is sorted and unique, inside `[0, n_rows - 1]`.
- `nonempty_bands` is the number of bands in `rule_bands` with at least one
  word center strictly right of x inside the table, counted before
  classification. It is recomputable and never smaller than
  `len(label_assignments)`.
- At most one `SubruleLabelAssignment` per `grid_row`; `grid_row` is unique,
  sorted, and a member of `rule_bands`.
- Each assignment's `physical_cell_ref` resolves to a real `DetectedCell`;
  `word_ids` is non-empty, in reading order, every center strictly right of x
  and inside that cell (same 0.8pt tolerance as `_assign_words`);
  `selected_run_bbox` is exactly the union of those word bboxes.
- The selected run is the nearest word run immediately right of x inside the
  same physical cell. Run splitting uses the existing `cell_gap_pt` rule from
  `_alignment_grid` (`structure.py:551-553`). Two runs at equal distance are a
  tie: `subrule_run_tie`, unresolved.
- Only runs classified as `short_label` by §6.3 appear. A band with no
  right-side word is excluded from numerator and denominator.
- `short_label_ratio = len(label_assignments) / nonempty_bands`, with
  `nonempty_bands > 0`. Missing, duplicate or out-of-band assignments are
  errors. The validator recomputes both the count and the ratio.

**`LabelAlignedEvidence` ratio.**

- `grid_rows` is the sorted, unique set of body bands (`header_rows <= r <
  n_rows`) where a gutter exists at x and no word crosses x; `gutter_bands =
  len(grid_rows)`.
- `nonempty_bands` is the number of body bands with at least one word anywhere
  in the table, recomputed from the fresh parse.
- `gutter_ratio = gutter_bands / nonempty_bands` with `nonempty_bands > 0`; a
  stored ratio that does not recompute within `1e-9` is
  `boundary_evidence_mismatch`.
- `word_ids` is the reading-order list of words in the gutter bands that do not
  cross x; each id must resolve and lie inside the table.

**`StructuralEdgeEvidence` de-duplication (S3).**

- Refs are sorted by `(grid_row, cell_index, edge)` and the same tuple appears
  at most once; a duplicate is `boundary_evidence_duplicate_ref`.
- At most one ref per `(grid_row, edge)`; two refs for the same row and edge
  must agree on x within tolerance or the candidate is unresolved.
- "Repeats in at least two row bands" means at least two distinct `grid_row`
  values after de-duplication, not two cells in one row.
- Every ref resolves; its edge x is within `visual_boundary_tol_pt` of the
  logical x; `physical_rule_component_ids` is a subset of `region_components`.

**`TableBBoxEvidence` is anchored to a fresh parse (N3).**

- `page_number` and `table_bbox` are copied verbatim from the fresh
  `DetectedTable`; the validator requires exact equality with the fresh parse
  (integer page, float bbox; no per-evidence bbox is allowed).
- `edge` selects `table_bbox[0]` (left) or `table_bbox[2]` (right); x must equal
  that value within `visual_boundary_tol_pt`.
- A page-number or bbox mismatch is `boundary_evidence_stale`, not a warning.
  The evidence may not define its own coordinate system.
- Only outer boundaries may use this kind.

**`RegionExtentEvidence` has a defined encoding (N3).**

The current parser constructs `implied_outer` at
`table_regions.py:282-288` with `values = (left, right)` and
`component_ids = tuple(member.component_id for member in members)`; a region
emits at most one such record. The evidence records that encoding instead of
relying on positional convention:

- `implied_outer_evidence_index` is the index into the fresh
  `TableRegion.evidence` tuple where `kind == "implied_outer"`.
- `implied_outer_values` equals that record's `values` exactly;
  `extent_left == implied_outer_values[0]` and
  `extent_right == implied_outer_values[1]`.
- `region_component_ids` equals that record's `component_ids` as a set, sorted.
- `boundary_source` equals the fresh `TableRegion.boundary_source` and is one
  of `implied_horizontal`, `implied_alignment`, `mixed`.
- `page_number` equals the fresh region page; `edge` selects `extent_left` or
  `extent_right`, and x must equal it within `visual_boundary_tol_pt`.
- If the fresh parse has no `implied_outer` record, the evidence is invalid:
  fail closed with `boundary_evidence_missing_ref`. Never infer the extent from
  the bbox.
- Only outer boundaries may use this kind.

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
| `subrule_promoted` | `subrule_promoted`, with `nonempty_bands >= 2` and at least one `label_assignments` entry |
| `header_canopy` | `header_canopy`, with both anchors |
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
| `subrule_promoted` | `visual_boundary_index`, non-empty `rule_bands`, `nonempty_bands > 0`, `label_assignments` | same visual checks; coverage `< visual_full_height_coverage`; `rule_bands` inside grid rows; `grid_row`s unique and inside `rule_bands`; `len(label_assignments) >= logical_subrule_promote_min_bands`; `short_label_ratio` recomputed from the assignments equals the stored value and is `>= logical_subrule_promote_min_ratio`; every word id exists, is right of `x`, and is in its declared physical cell; `selected_run_bbox` is the word union. Missing/duplicate band -> `boundary_evidence_duplicate_ref`; ratio mismatch -> `boundary_evidence_mismatch`; run tie -> `subrule_run_tie`. |
| `header_canopy` | `level`, `boundary_edge`, both anchor refs, non-empty left/right ref lists, `left_label`, `right_label` | every ref resolves to a `DetectedHeaderCell` by `(level, source_row, source_column, column)`; all refs have `level == evidence.level`; `level < header_rows`; bbox inside the table; the left refs lie at or left of `x`, the right refs at or right; anchors are the nearest cells on their side and satisfy the `boundary_edge` position rule; labels equal the anchors' normalized text and are distinct; two same-level cells touching `x` -> `header_level_tie`; missing side -> `header_missing_for_canopy`. |
| `label_aligned` | non-empty `grid_rows`, non-empty `word_ids` | rows in `[header_rows, n_rows)`; every word id exists on the page and inside the table; no word crosses `x`; `gutter_ratio` recomputes from `gutter_bands` and `nonempty_bands`; `gutter_ratio >= logical_label_min_band_ratio`; `len(grid_rows) >= logical_label_min_bands`. |
| `structural` | non-empty `physical_cell_edge_refs` | each ref resolves to a real `DetectedCell`; refs are sorted and unique; at most one per `(grid_row, edge)`; the edge is within tolerance of `x`; at least two distinct `grid_row` values remain after de-duplication; no word crosses `x`. `physical_rule_component_ids`, when present, must all be in `region_components`. Duplicate -> `boundary_evidence_duplicate_ref`. |
| `table_bbox` | `edge`, `page_number`, `table_bbox` | only for outer boundaries; `page_number` and `table_bbox` equal the fresh `DetectedTable` exactly; `x` equals `table_bbox[0]` (left) or `table_bbox[2]` (right) within tolerance. Stale page/bbox -> `boundary_evidence_stale`. An internal boundary may not use this kind. |
| `region_extent` | `edge`, `page_number`, non-empty `region_component_ids`, `extent_left`, `extent_right`, `boundary_source`, `implied_outer_evidence_index`, `implied_outer_values` | only for outer boundaries; `implied_outer_evidence_index` selects a fresh `TableRegion.evidence` record of kind `implied_outer`; `implied_outer_values == values`, `extent_left == values[0]`, `extent_right == values[1]`; `region_component_ids` equals that record's `component_ids` set; `boundary_source` equals the fresh region source and is in `{implied_horizontal, implied_alignment, mixed}`; `x` equals the selected extent within tolerance. Missing record -> `boundary_evidence_missing_ref`; mismatch -> `boundary_evidence_stale`. Never infer an extent from the bbox. |

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

**Canonical row bands (S2, N6).** The projection is derived per logical column
as follows:

1. For each physical row `r` in `[0, n_rows - 1]`, compute the set
   `S(r)` of physical column indices whose interval has positive width overlap
   with the logical interval.
2. Split `[0, n_rows - 1]` at every row where `S(r)` changes. The resulting
   maximal runs are the rows of the projection; adjacent runs never carry the
   same `S`.
3. Emit one `PhysicalColumnOverlap` per (run, physical column in `S`), sorted
   by `(grid_row_start, physical_column)`.
4. The runs of one logical column partition `[0, n_rows - 1]` exactly: no gap,
   no overlap, first `grid_row_start == 0`, last `grid_row_end == n_rows - 1`.
5. Inside a run, physical columns are unique and ascending.

This is the "complete projection" rule: every logical column is projected over
every physical row, not only the rows where text happens to exist. A missing
or non-canonical band is `mapping_row_band_not_canonical`; a gap or overlap is
`mapping_row_band_overlap`.

**Overlap geometry is recomputable.** For a logical interval `[L, R]` and
physical interval `[grid.xs[i], grid.xs[i + 1]]`:

```text
overlap_left  = max(L, grid.xs[i])
overlap_right = min(R, grid.xs[i + 1])
overlap_fraction = (overlap_right - overlap_left)
                   / (grid.xs[i + 1] - grid.xs[i])
```

The validator recomputes all three from the fresh `grid.xs` and the
authoritative logical interval. Absolute tolerance `1e-6` for coordinates and
fraction; a zero or negative overlap is `mapping_physical_overlap_missing`. An
`overlap_fraction` outside `(0, 1]` is `boundary_evidence_mismatch`.

**Visual intervals are reconstructed, not guessed (S2).**

When `visual_columns is not None`, `visual_boundaries` is sorted and

```text
len(visual_boundaries) == visual_columns + 1
visual interval i = [v[i], v[i + 1]]   for every 0 <= i < visual_columns
```

Membership is decided by positive width, never by point placement, so the
endpoint convention cannot change the index set:

```text
logical interval [L, R] overlaps visual interval i iff
min(R, v[i + 1]) - max(L, v[i]) > 0
```

Touching at a single x (zero width) is not an overlap, so the half-open/closed
convention only removes ambiguity for a point and cannot change the index set.
`visual_column_indices` is the sorted, unique list of intervals with positive
overlap. It is empty when `visual_columns is None`. A length mismatch between
`visual_boundaries` and `visual_columns` is
`mapping_visual_interval_mismatch`.

`ColumnProjection` is the **only authoritative** projection payload. It lives
once on the table in `column_projection`, ordered by `logical_column`. A
proposed `LogicalColumn` does not embed a copy. The validator enforces
one-to-one order, `column_projection[i].logical_column == i`, and
`column_projection[i].left == logical_boundaries[i]`,
`column_projection[i].right == logical_boundaries[i + 1]` for a resolved table.

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

`role_header_cell_ref` and `role_header_cell_id` are two forms of the same
link, not alternatives. They may coexist; there is no "at most one" rule. The
validator enforces this matrix per record:

| `role_source` | `role_header_cell_ref` | `role_header_cell_id` | Additional rule |
| --- | --- | --- | --- |
| `header_text` | required at parser level | required after rebuild | both, when present, resolve to the same header cell |
| `subrule_short_label` | must be null | must be null | `role == condition` |
| `heuristic` | optional | optional | if present, must resolve; no header claim |
| `fail_closed` | must be null | must be null | `role == unknown` |

At parser level the domain id does not exist yet, so only the ref is required;
after rebuild the id is required and the ref is still carried. Both-null is
valid only for `subrule_short_label`, `fail_closed`, and `heuristic`;
`header_text` with both null is `header_role_source_invalid`. A ref/id pair
that resolves to different cells is `boundary_evidence_mismatch`.
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

**LogicalCell reconstruction contract (N6).** The following rules are
normative; an independent reader must be able to rebuild each field.

*1. Rowspan, colspan and cell decomposition.*

- One `DetectedCell` covers rows `grid_row .. grid_row + row_span - 1` and
  physical columns `column_index .. column_index + column_span - 1`.
- Assign each of its words to exactly one logical column by center x (§7.3);
  words with no assigned word produce no logical cell.
- Take the maximal consecutive runs of logical columns that contain at least
  one assigned word. Each run yields one logical-cell candidate:
  `logical_column` = run start, `logical_column_span` = run length, and
  `word_ids` = the cell's words in those columns.
- Candidates from different physical cells with the same
  `(row_start, row_end, logical_column, logical_column_span)` are merged into
  one `LogicalCell`; `physical_cells` lists one `PhysicalCellAssignment` per
  source cell. This is the only merge. Adjacent rows are never merged, and
  cells with different row coverage are never merged.
- `row_start = grid_row`, `row_end = grid_row + row_span - 1`; the range is
  contiguous by construction.
- `logical_column_span` counts the columns that actually carry assigned words;
  it is not `DetectedCell.column_span`. The physical span remains on the
  detected cell.
- Within one logical column, logical-cell row ranges must be disjoint. An
  intersection is `mapping_row_overlap` and the table is unresolved.
- `kind = "header"` iff `row_end < header_rows`, `"data"` iff
  `row_start >= header_rows`; a cell crossing the header boundary is
  `logical_cell_kind_boundary` and unresolved.

*2. bbox.*

`LogicalCell.bbox` is the union of the bboxes of its assigned words (content
extent). It is not the physical cell bbox, not the intersection with the
logical column, and not a synthetic column rectangle. A word whose bbox
slightly crosses the logical interval is still included because attribution is
by word center. The validator recomputes the union from `word_ids`.

*3. text and word order.*

`LogicalCell.text` is `_words_to_text(assigned_words)` from
`structure.py:335-352`, applied to exactly the assigned words:

- sort by `((y0 + y1) / 2, x0)`;
- group into lines with `line_tol = max(2.0, median(word_height) * 0.55)`;
- join words inside a line with one ASCII space in x order;
- join lines with `\n`; strip the result.

`word_ids` and each assignment's `word_ids` are stored in this reading order.
A split cell's text is therefore a re-rendering of its word subset, never a
prefix or slice of the physical cell's text.

*4. logical_cell_id.*

`table_id` is the domain id built by `build_table`:
`f"p{page_number:03d}-t{table_index:02d}"` (`table_rebuilder.py:17`), where
`table_index` is the 1-based ordinal of the table on its page. The id is:

```text
logical_cell_id = f"{table_id}-lc-{kind}-r{row_start:02d}-r{row_end:02d}"
                  f"-c{logical_column:02d}-s{logical_column_span:02d}"
```

It contains no text, word content, metric, or traversal counter. The S2b
derivation receives the same `(page_number, table_index)` pair that is later
passed to `build_table`; the rebuild must reproduce the same ids. Duplicate ids
within a table are `logical_cell_id_collision`.

*5. Word universe.*

The authoritative universe is the set of words assigned to `grid.cells`,
excluding `grid.unassigned_words`:

- a word is assigned to the first cell in `grid.cells` enumeration order whose
  bbox contains its center with the existing 0.8pt inclusive tolerance
  (`_assign_words`, `structure.py:313-333`);
- a word inside the table bbox but in no cell goes to `unassigned_words` and is
  excluded from the partition; its count is reported, not silently dropped;
- S2b-Schema may extend `_assign_words` to return
  `cell_index -> tuple[word_id, ...]` in the same pass, but must not change its
  iteration order, tolerance or cell fields;
- an independent audit recomputes the universe from a fresh parse with the same
  page, `layout.words` order, center formula and first-match rule. The union of
  all logical assignments must equal it; a missing word is
  `mapping_word_not_assigned`, an extra or duplicated word is
  `mapping_word_partition_mismatch`.

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

**Strict snapshot validation (N8).** A computable SHA does not make a snapshot
legal. Add:

```text
validate_table_params_snapshot(snapshot: dict, *, expected_version: str) -> list[str]
```

It rejects, in order:

1. top-level keys not exactly `{"snapshot_version", "params"}`;
2. `snapshot_version` different from `expected_version` read from the manifest
   or `run_config`;
3. `params` keys not exactly the field set of that version;
4. a missing, extra, unknown or duplicate key; duplicate JSON object keys are
   rejected at load time (`object_pairs_hook`) before hashing;
5. a value with the wrong JSON type or a non-finite number;
6. only after 1–5 pass is `snapshot_sha256(snapshot)` compared with the stored
   hash.

A snapshot that fails 1–5 is `table_params_snapshot_schema_invalid` even if its
SHA matches itself. A stored version different from the manifest/run_config
version is `table_params_snapshot_version_mismatch`.

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
   A version mismatch between the snapshot and the manifest/run_config is
   `table_params_snapshot_version_mismatch`.
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

**S2b-Schema edit boundary (N8).** "Do not modify S1/S2a" is refined into an
explicit allowlist so the implementing agent does not decide case by case:

| File | Allowed S2b-Schema change | Forbidden |
| --- | --- | --- |
| `src/icpdf/parser/config.py` | add the seven defaults; bump the version constant; add `V1_FIELDS` / `V2_FIELDS`, version-aware helpers and the strict validator | changing existing defaults or the v1 field list |
| `src/icpdf/parser/pipeline.py` | pass the version explicitly to snapshot/helpers | changing detection, extraction or run layout |
| `tools/audit_visual_primitives.py` | add read-only version dispatch and snapshot-schema validation | changing `verify_identity`, primitive/segment reconstruction, `GRID_TOL` binding or boundary checks |
| `tools/validate_evidence.py` | add the same read-only dispatch | changing existing checks or tolerances |
| `src/icpdf/parser/table_detector.py`, `structure.py` | additive logical fields; `_assign_words` may return its assignment mapping | changing `grid.xs`/`grid.ys`, cell construction, word assignment order or tolerance |
| `src/icpdf/parser/table_rebuilder.py` | fill logical ids/fields additively | changing existing table/row/cell/header id formats |
| `src/icpdf/parser/rule_primitives.py`, `visual_structure.py`, `table_regions.py` | none | any edit |
| `configs/parser.yaml`, Gold v1/v2, S1/S2a reports | none | any edit |

This is a compatibility layer only. S2a's primitive reconstruction, identity
gate and visual evidence checks stay byte-for-byte equivalent on old artifacts.

Required compatibility tests (S2b-Schema):

- replay a stored v1 snapshot and reproduce `82d4df4d...`;
- assert the v1 replay has no `logical_*` key;
- assert a v2 snapshot contains the seven new keys;
- delete one v2 key, add one unknown key, and duplicate a JSON key: each must
  be refused although a SHA can still be computed;
- a snapshot version that disagrees with the manifest is refused;
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

**Fixed-anchor grouping (N4).** Grouping is deterministic and cannot chain:

1. Sort candidates by `(x, source_rank, evidence_id)`, with `source_rank`
   `outer < grid < visual < header < gutter` and `evidence_id` the stable
   index/id inside that source. The sort is total; equal keys are impossible
   after de-duplication.
2. Take the first ungrouped candidate as the **anchor**. A candidate joins the
   group iff `abs(x - anchor_x) <= visual_boundary_tol_pt`. Always compare with
   the anchor, never with the previous member.
3. When a candidate exceeds the anchor distance, close the group and make that
   candidate the anchor of the next group.
4. The internal group x is the arithmetic mean of the member x values, with no
   rounding. Example: x = 100.0, 102.0, 104.0 with tolerance 2.5 yields
   `{100.0, 102.0}` and then `{104.0}`, never one chain of three.
5. `anchor_x` and every member `source_xs` are stored on the decision, sorted
   and unique. No source x is dropped or rewritten.
6. An outer boundary is its own group and its x is the table bbox edge, never
   the mean. A candidate within tolerance of an outer edge is folded into that
   outer group as extra evidence and is never kept as an internal boundary.
7. Candidates outside the table bbox are discarded and recorded in the
   decision diagnostics.

This prevents several weak, non-coincident sources from being chained into one
strong boundary.

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

The promotion test is the approved S2 rule, with the ratio defined exactly:

1. for each row band the rule intersects, the **source cell** is the unique
   `DetectedCell` whose bbox contains `x` (`bbox[0] <= x <= bbox[2]`) and whose
   row coverage includes that band. Zero source cells means no label candidate
   in that band; more than one is `subrule_source_cell_ambiguous` and the
   candidate is `unresolved`;
2. inside the source cell take the words whose center is strictly right of x,
   sort them by `(x0, word_id)`, and start a new run whenever the gap to the
   previous word exceeds `cell_gap_pt` (`structure.py:551-553`);
3. select the run with the smallest left edge; runs whose left edges differ by
   at most `1e-6` are a tie (`subrule_run_tie`) and the candidate is
   `unresolved`; never pick a run by word count or text;
4. classify the selected run with §6.3.1; only `short_label` counts;
5. `nonempty_bands` = bands with at least one word center strictly right of x
   anywhere inside the table, computed before classification;
6. `short_label_bands` = `len(label_assignments)`;
7. `short_label_ratio = short_label_bands / nonempty_bands` with
   `nonempty_bands > 0`; bands with no right-side word are excluded from both
   numerator and denominator and a band is never counted twice;
8. promote iff `short_label_ratio >= logical_subrule_promote_min_ratio` (0.50)
   **and** `short_label_bands >= logical_subrule_promote_min_bands` (2);
9. `logical_subrule_ambiguous_min_ratio <= ratio < 0.50` with at least 2
   non-empty bands is `unresolved`, not a demotion (lower bound inclusive,
   upper bound exclusive);
10. `nonempty_bands == 0` yields no ratio and no promotion; the candidate falls
    through to the no-evidence branch unless another source supports it.

#### 6.3.1 Lexical classes (N5)

Normalization: strip, collapse internal whitespace, and casefold only for
keyword matching; the stored label keeps its original text.

| Class | Test (checked in this order) |
| --- | --- |
| `numeric` | every token parses as a number with optional sign, decimal point, exponent or `%`; no letter outside `%` |
| `value_with_unit` | one numeric token followed only by tokens from `LOGICAL_UNIT_TOKENS`, with no relational marker, e.g. `5 V`, `10 kΩ`, `±0.5 %`. This is data, not a condition |
| `unit_only` | one token (optionally with a digit prefix such as `10k`) whose alphabetic part is in the frozen `LOGICAL_UNIT_TOKENS` set |
| `identifier` | one token matching `[A-Za-z][A-Za-z0-9_/-]*` that contains a digit or `_`/`/`, with no whitespace |
| `short_label` | at most `logical_short_label_max_words` words and `logical_short_label_max_chars` characters, at least one letter, no digit, and not `unit_only` |
| `condition_expression` | contains at least one relational marker: a comparison operator (`<`, `<=`, `>`, `>=`, `=`, `±`, `≈`, `≤`, `≥`); a range connector (`to`, `..`, `–`, `—`, `through`) between two value-with-unit phrases; or a supply/temperature symbol bound by one of those operators (`TA = 25 °C`, `VCC = 5 V`, `VIL < 0.8 V`) |
| `field_name` | a plain noun phrase with no marker above, e.g. `Output Voltage`, `Clock Source`, `Data Format`, `Input Range`, `Operating Mode` |
| `prose` | more than six words or sentence punctuation; condition-like only if a relational marker above is present |

`LOGICAL_UNIT_TOKENS` is a frozen code constant, not a YAML entry. Its initial
closed set is:

```text
V, mV, µV, uV, kV, A, mA, µA, uA, nA, W, mW, µW, kW,
Ω, kΩ, MΩ, ohm, Hz, kHz, MHz, GHz, s, ms, µs, us, ns, ps,
F, pF, nF, µF, uF, mF, H, nH, µH, %, °C, °F, K, dB, dBm,
LSB, ppm, V/V, A/A, °, rad, S, mS, µS
```

The set may be extended only with a new design review; it may not be tuned
after seeing S2b results.

**Only `condition_expression` is condition-like.** `field_name` and marker-free
`prose` are never demoted to `condition_path` merely because they contain
letters or are longer than a short label.

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
- "Condition-like" means the right-side run is classified
  `condition_expression` by §6.3.1 and carries at least one **relational**
  marker (comparison operator, range connector, or a supply/temperature symbol
  bound by such an operator). A `field_name` such as `Output Voltage` or
  `Clock Source`, a marker-free `prose` run, `numeric`, `value_with_unit`,
  `unit_only` and `identifier` are **not** condition-like; `5 V` alone is a
  data value. This is the only content test in S2b; it does not read a cell's
  semantic category.
- If the lexical class is ambiguous or the run has no explicit marker, the
  candidate is `demote_no_evidence`; it is never promoted to `condition_path`
  by default. `condition_path` requires a positive marker, not the absence of a
  short-label match.
- `condition_path` is a **path label** for S2c. S2b emits no `ConditionBand`
  and no `ConditionContext`; it only preserves the demoted x, its row bands and
  its support for the later S2c stage.

A boundary that has both printed-rule evidence and no explicit condition marker
remains `demote_no_evidence`; a boundary that is condition-like but also
ambiguous (`[0.25, 0.50)`) remains `unresolved`, not
`demote_condition_path`. The order is: promote, then ambiguous, then
condition-path only with a marker, then no-evidence. A content class never
overrides the ratio branch.

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

For each logical column `[left, right]`, the canonical row bands of §5.4 define
the row ranges; within each band, record the positive overlaps with every
physical column interval `[grid.xs[i], grid.xs[i + 1]]`. `overlap_fraction` is
recomputed from `overlap_left/right` and the physical width; a mismatch is an
error, not a warning. The bands of one logical column partition
`[0, n_rows - 1]` exactly and adjacent bands never carry the same physical
column set.

`physical_column` plus `physical_left` / `physical_right` is the locator.
`grid_row_start` / `grid_row_end` is the canonical band, not an arbitrary text
extent.

### 7.3 Cell projection and word assignment

1. For each row and logical column, find physical cells whose bbox has a
   positive-width intersection with the logical interval.
2. Assign each `TextWord` by its exact center x:
   `cx = (bbox[0] + bbox[2]) / 2`. Every logical column uses the left-open,
   right-closed interval `(b[i], b[i + 1]]`; the single point `cx == b[0]` on
   the left outer edge is assigned to column 0. A center exactly on an internal
   boundary (`cx == b[i]`) therefore belongs to the left column `i - 1`. There
   is **no epsilon and no rounding**: coordinates are
   compared as stored floats. A non-finite center is `mapping_word_not_assigned`
   and the table is unresolved. Every exact-boundary hit is counted in the
   diagnostics as `word_boundary_tie`, but the assignment is still the one
   above.
3. Decompose physical cells into logical cells by §5.6: one logical cell per
   (physical cell, maximal consecutive run of word-bearing logical columns),
   merged only when `(row_start, row_end, logical_column,
   logical_column_span)` is identical. A physical cell straddling a boundary
   appears in several `PhysicalCellAssignment`s with the same
   `PhysicalCellRef` and disjoint word subsets; no word is duplicated.
4. `word_ids` across all logical cells are a disjoint partition of the word
   universe defined in §5.6, item 5.

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
- For each logical column `[L, R]` and each level, compute the x-overlap width
  of every header cell at that level:

  ```text
  width(cell) = max(0, min(cell.bbox[2], R) - max(cell.bbox[0], L))
  ```

  Only cells with `width > 0` are candidates. The winner is the maximum width;
  two candidates whose widths differ by at most `1e-6` are a tie, and the table
  is `unresolved` (`header_level_tie`). Width, not area or bbox centre, is the
  only criterion.
- `header_path` is the top-to-bottom list of winning labels, ordered by
  `level`. Missing levels are skipped, not filled from neighbours;
  `header_cell_refs` is parallel to `header_path` and records exactly which
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
- A table with no header at all may still get a `resolved` logical lattice from
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
  header_rows`; the cell belongs to this table. For `header_canopy`, every left
  ref satisfies `bbox[2] <= x + tol`, every right ref `bbox[0] >= x - tol`, the
  anchors satisfy the `boundary_edge` rule of §5.3, and `left_label` /
  `right_label` equal the anchors' normalized text.
- `subrule label_assignments`: `grid_row`s are unique and inside `rule_bands`;
  each `physical_cell_ref` resolves; each word id is in that cell and strictly
  right of x; `selected_run_bbox` equals the word union; `nonempty_bands` and
  `short_label_ratio` recompute from the fresh parse.
- `table_bbox`: `page_number` and `table_bbox` equal the fresh `DetectedTable`
  exactly; a mismatch is stale, not a warning.
- `region_extent`: `implied_outer_evidence_index` selects a fresh
  `TableRegion.evidence[kind="implied_outer"]`; `implied_outer_values`,
  `extent_left/right`, `region_component_ids`, `boundary_source` and
  `page_number` match that record.
- `grid_rows`: in `[header_rows, n_rows)`; each row is a real band; no row is
  repeated.
- `word_ids`: each id exists exactly once on the page; its center is inside the
  referenced physical cell bbox (same 0.8pt tolerance as `_assign_words`) and
  inside the logical cell bbox. Across every `PhysicalCellAssignment` of the
  table a word id appears at most once. If one physical cell is referenced by
  more than one logical cell, those assignments must carry disjoint `word_ids`
  sets; the union over the table equals the recomputed word universe of §5.6.
- `physical_cell_edge_refs`: `(grid_row, cell_index)` resolves to a real
  `DetectedCell`; `column_index` matches; the edge x is within tolerance of the
  logical boundary; refs are unique and sorted, and at least two distinct
  `grid_row` values remain.
- `physical_column`, `physical_left`, `physical_right`: `physical_column` is a
  valid interval index; `physical_left == grid.xs[i]` and `physical_right ==
  grid.xs[i + 1]`; the canonical bands of one logical column partition
  `[0, n_rows - 1]` with no gap, overlap or duplicate band; `overlap_left`,
  `overlap_right` and `overlap_fraction` recompute from the authoritative
  logical interval and physical width within `1e-6`.
- `visual_column_indices`: `len(visual_boundaries) == visual_columns + 1` when
  not `None`; indices are sorted, unique and in range; each has positive width
  overlap by the §5.4 rule.
- `region_component_ids`: every id is in `region_components`; for
  `region_extent`, the structured fields match the fresh `TableRegion`
  evidence as above.

### 9.3 Independent reconstruction of a logical cell

Given a persisted `LogicalCell`, an independent reader can rebuild it without
running the S2b decision logic:

1. take `physical_cells`; for each `PhysicalCellAssignment`, resolve
   `PhysicalCellRef` to a physical cell and take exactly the listed `word_ids`;
2. resolve each word id to its `TextWord` (page, block, line, bbox) and check
   its center lies inside the physical cell and inside the logical cell bbox;
3. recompute `bbox` as the union of the assigned word bboxes; it must equal
   `LogicalCell.bbox`;
4. recompute `text` with `_words_to_text` over the assigned words
   (`structure.py:335-352`); it must equal `LogicalCell.text`;
5. take the union of all assignment word ids in stored reading order; it must
   equal `LogicalCell.word_ids`;
6. across all logical cells of the table, the assignment word ids must be
   pairwise disjoint and must cover exactly the word universe of §5.6
   (`unassigned_words` excluded);
7. the same physical cell may appear in several assignments, but the word
   subsets must be disjoint. This is the check that a shared physical cell was
   split, not duplicated;
8. check `row_start/row_end` equal the source cell's grid coverage, the
   `logical_column/span` equal the word-bearing run, and `kind` follows the
   `header_rows` rule;
9. recompute `logical_cell_id` from the §5.6 formula and the same
   `(page_number, table_index)`; it must equal the stored id.

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
boundary_evidence_duplicate_ref
subrule_run_tie
subrule_source_cell_ambiguous
word_boundary_tie
mapping_physical_overlap_missing
mapping_lattice_index_mismatch
mapping_row_band_not_canonical
mapping_row_band_overlap
mapping_visual_interval_mismatch
mapping_row_overlap
mapping_word_not_assigned
mapping_word_partition_mismatch
logical_cell_kind_boundary
logical_cell_id_collision
header_level_tie
header_missing_for_canopy
header_role_source_invalid
region_lattice_inconsistent
unsupported_table_params_snapshot_version
table_params_snapshot_schema_invalid
table_params_snapshot_version_mismatch
```

A table may carry several codes. Codes are evidence for review, not an
alternative decision mechanism. `word_boundary_tie` is diagnostic only: it
records an exact center-on-boundary hit whose assignment is still the
deterministic left-column rule of §7.3, so it does not make a table
`unresolved`.

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
   `logical_columns`, `column_projection[i].logical_column == i`, each
   `ColumnProjection` has a non-empty `physical_columns`, and `left` / `right`
   equal `logical_boundaries[i]` / `logical_boundaries[i + 1]`.
5. Every `PhysicalColumnOverlap.physical_column` is a valid index into the
   table's one `grid.xs`; `physical_left == grid.xs[i]`,
   `physical_right == grid.xs[i + 1]`; the overlap is positive; the row band is
   inside `[0, n_rows - 1]`. Per logical column, the bands are canonical
   (§5.4): they partition `[0, n_rows - 1]`, never overlap, never leave a gap,
   and adjacent bands never carry the same physical column set; within a band
   physical columns are unique and ascending.
6. `overlap_left`, `overlap_right` and `overlap_fraction` recompute from the
   authoritative interval and physical width within `1e-6`; every logical
   column overlaps at least one physical column and every physical column
   overlaps at least one logical column.
7. On a resolved table, `len(visual_boundaries) == visual_columns + 1` when not
   `None`; every `visual_column_indices` entry is in
   `[0, visual_columns - 1]`, sorted, unique, and has positive width overlap by
   §5.4; the tuple is empty iff `visual_columns is None`.
8. Every kept boundary's evidence resolves per §5.3/§9.2; a missing reference
   is an error, not a warning. The evidence kind must match the declared
   source. `header_canopy` is directed: both anchors resolve, left/right lists
   are on the correct side, labels equal the anchor text, and the
   `boundary_edge` position rule holds. `subrule_promoted` has unique in-band
   assignments and a recomputable ratio. `table_bbox` and `region_extent` match
   the fresh parse; self-consistency alone is not accepted.
9. Candidate decisions obey fixed-anchor grouping: `anchor_x` is a member of
   `source_xs`; every `abs(x - anchor_x) <= visual_boundary_tol_pt`; group
   ranges do not overlap (`max(source_xs) < next_anchor_x`); no source x is
   dropped; an outer decision's x equals the table bbox edge and is not a mean.
10. `LogicalCell.physical_cells` is non-empty; every `PhysicalCellRef` resolves;
    each assignment's `word_ids` is non-empty; assignment word ids are pairwise
    disjoint and their union equals `LogicalCell.word_ids`; across the table
    the union equals the word universe of §5.6, item 5.
11. `LogicalCell.bbox` equals the union of its assigned word bboxes;
    `LogicalCell.text` equals `_words_to_text` over those words; `word_ids` is
    in that reading order; it is not an unmodified copy of a shared physical
    cell.
12. `LogicalCell.row_start/row_end` equal the source cell's grid coverage,
    `logical_column/span` equal the word-bearing run, `kind` follows
    `header_rows`, and `logical_cell_id` reproduces from §5.6. Within one
    logical column, logical-cell row ranges are disjoint.
13. Header references exist, belong to the table, and their levels are within
    `header_rows`; `role_source` is one of `header_text`,
    `subrule_short_label`, `heuristic`, `fail_closed`; the role-source/ref
    matrix of §5.5 holds; `subrule_short_label` requires `role = condition` and
    short-label evidence.
14. Physical and S2a fields are unchanged: `grid.xs`, `grid.ys`, cell bboxes,
    cell text, `column_index`, `row_span`, `column_span`, `visual_boundaries`,
    `visual_boundary_status`, `visual_columns`, `partial_boundaries`,
    `visual_boundary_evidence`.
15. Candidate ids and counts are unchanged; candidate logical refs are empty on
    unresolved tables.
16. Old run artifacts without logical fields still load and are treated as
    `unresolved`, not as a parse failure.
17. A replayed `table-params/v1` snapshot reproduces the frozen v1 SHA and
    contains no `logical_*` key; a v2 snapshot contains exactly `V2_FIELDS`
    (the 20 v1 names plus the seven `logical_*` names). Both pass strict key,
    type and version validation (§5.8), not only a hash comparison.

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

### 12.2 Gold annotation state and ambiguity overlay (P1-5, N7)

Gold annotation state, Gold ambiguity and algorithm uncertainty are three
separate axes. They are stored separately and are never collapsed into one
status field with a precedence rule.

**Algorithm axis (on the predicted table):**

```text
logical_mapping_status = "resolved" | "unresolved"
```

**Gold annotation axis (on the evaluation manifest, not on the Gold file):**

```text
gold_annotation_state = "typed_decided" | "typed_undecided" | "untyped_legacy"
```

- `typed_decided`: the table carries a non-null typed `logical_columns` in a
  typed (v2) Gold set.
- `typed_undecided`: the table explicitly records `logical_columns: null` in a
  typed (v2) Gold set.
- `untyped_legacy`: the table has no typed logical field at all (all v1
  tables). It is excluded from every logical metric; it remains in detection,
  row, cell-text and visual metrics. The evaluator must not use the
  `gold_table.get("logical_columns", gold_columns)` fallback for S2b logical
  metrics.

**Gold ambiguity axis (on the evaluation manifest, not on the Gold file):**

```text
gold_ambiguity_status = "none" | "open"
```

`open` means an `s2b-ambiguity/v1` overlay entry with the same `item_id`
exists. This axis is orthogonal to the annotation state: a v1 table can be
`untyped_legacy` and still carry an open ambiguity, and a v2 table can be
`typed_decided` while its logical reading is disputed.

**Cross-product and expected algorithm outcome.** Each manifest item occupies
exactly one row; no state overrides another:

| `gold_annotation_state` | `gold_ambiguity_status` | Expected | Reported in |
| --- | --- | --- | --- |
| `typed_decided` | `none` | `resolved` exact match | logical metrics |
| `typed_decided` | `open` | `unresolved` | ambiguity bucket |
| `typed_undecided` | `none` | `unresolved` | undecided bucket |
| `typed_undecided` | `open` | `unresolved` | ambiguity bucket |
| `untyped_legacy` | `none` | not asserted | detection / visual only |
| `untyped_legacy` | `open` | `unresolved` | ambiguity bucket |

Manifest validation is strict and read-only:

- `typed_decided` and `typed_undecided` are assignable only to an `item_id`
  that belongs to a typed (v2) Gold set; the validator rejects either state on
  a v1 item.
- `untyped_legacy` is assignable only to a table whose Gold record has no
  logical field; the validator rejects it for a v2 table that carries
  `logical_columns` or an explicit `null`.
- `gold_ambiguity_status == "open"` requires exactly one overlay entry for that
  `item_id`; `"none"` requires zero entries. Both are checked without editing
  Gold.
- An `open` item is never counted as a resolved exact match, whatever its
  annotation state: it stays out of every exactness denominator and appears in
  the ambiguity bucket together with its predicted
  `logical_mapping_status`.

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
- Every overlay entry sets `gold_ambiguity_status = "open"` for its `item_id`;
  it does not change that item's `gold_annotation_state`.
- An `open` item is excluded from every exactness denominator and reported in
  the ambiguity bucket; it is never counted as a resolved exact match.
- `LM358-P04-T02` is retained as the case where `role = unknown` is correct;
  the design must not "fix" it by inventing a label.
- An `open` item may be included in the negative/ambiguous detection set.
  The only assertion there is `logical_mapping_status == "unresolved"`; the
  evaluation never requires the algorithm to pick one of the competing Gold
  interpretations, and never asserts a made-up logical column count.
- The overlay is frozen with the S2b set; later additions require a new
  `s2b` evaluation version.

### 12.3 Metrics

| Metric | Definition | Denominator |
| --- | --- | --- |
| LogicalBoundary precision / recall | matched kept boundaries within 2.5pt vs Gold logical `column_boundaries` | predicted / Gold boundaries on `typed_decided` + `none` tables with typed boundaries |
| LogicalColumn exact match | predicted count and ordered intervals equal Gold `column_boundaries` | `gold_annotation_state == "typed_decided"` and `gold_ambiguity_status == "none"` |
| Physical→logical mapping exact match | each logical column's physical column set, `physical_left/right` and row-band overlaps equal the S2b-set annotation | S2b-set cases with an annotated projection, `gold_ambiguity_status == "none"` |
| LogicalCell projection exact match | row range, logical column span, physical cell set and per-cell word partition equal the S2b-set annotation | S2b-set annotated projection cases, `gold_ambiguity_status == "none"` |
| Header provenance coverage | logical columns with a complete, existing header cell chain | labelled logical columns on `typed_decided` + `none` tables |
| Undecided handling | predicted `unresolved` on explicitly undecided tables | `gold_annotation_state == "typed_undecided"` |
| Ambiguous detection recall | predicted `unresolved` on gold-ambiguous cases | `gold_ambiguity_status == "open"` (reported separately) |
| Zero-regression | S1/S2a/candidate fields byte-identical | all regression tables |

The two Gold axes are joined by `item_id`; a metric that quotes only one of
them (for example "on decided tables") is underspecified and is rejected by the
report validator. `untyped_legacy` tables never appear in a logical
denominator, with or without an ambiguity overlay.

Report per-item results and a failure list; never report only a single exact
match. A boundary count match with a wrong physical mapping is a failure, not a
pass. An item with `gold_ambiguity_status == "open"` is never counted as a
resolved exact match.

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
| S2b-Schema | models, additive fields, read-only validator, unit tests | no detector integration; no S1/S2a behaviour or Gold change; edits limited to the §5.8 allowlist | Reviewer checks schema, evidence union and snapshot compatibility |
| S2b-Prototype | logical lattice on the standalone S2b set | no pipeline integration; no extraction dependencies | Reviewer checks boundaries, mapping, word partition and failure behavior |
| S2b-Integration | detector/rebuilder integration, full regression, compatibility report | additive wiring only; no physical or S2a change | Reviewer checks zero regression and evidence completeness |

No stage may begin before the previous gate is approved. S2b-Integration is not
authorized by S2a freeze or by this design.

**S2b-Schema edit boundary.** The schema stage may change only the files listed
as allowed in §5.8. In particular it may add the version argument and strict
`V1_FIELDS`/`V2_FIELDS` validation in `config.py`, thread the snapshot version
through `pipeline.py`, add read-only version dispatch to the audit/validate
tools, and add optional logical fields plus an `_assign_words` return value.
It may not alter primitive collection, `GRID_TOL`, S2a visual derivation, the
evidence predicates, `grid.xs`/`grid.ys`, physical cell bbox/text, Candidate
IDs, or any Gold file. Read-only version detection in an existing audit
consumer is a compatibility exception, not permission to change S2a behaviour.
If a required change falls outside the allowlist, the stage stops and returns
to review.

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
8. Confirm the two Gold axes in §12.2 (`gold_annotation_state`,
   `gold_ambiguity_status`) and that all v1 tables are `untyped_legacy` for
   logical metrics, with the existing `n_columns` fallback never used as a
   logical annotation.
9. Confirm that `PhysicalColumnOverlap` is table-global (one `grid.xs` per
   table) and that cross-table aggregation is out of scope for S2b.
10. Approve the directed `HeaderCanopyEvidence` record (§5.3), including
    `boundary_edge`, the two anchor refs and the multi-cell membership rules.
11. Approve the per-band `SubruleLabelAssignment` record and the ratio formula
    in §6.3 as the only promotion evidence.
12. Approve `TableBBoxEvidence`/`RegionExtentEvidence` being validated against
    a fresh parse (`boundary_evidence_stale`), and the indexed
    `implied_outer` encoding in §5.3.
13. Approve fixed-anchor candidate grouping (§6.1) and the retained
    `candidate_x` / `anchor_x` / `source_xs` fields that make grouping
    auditable without re-grouping.
14. Approve the lexical classes and the frozen unit lexicon in §6.3.1, and the
    rule that a `field_name` or `prose` right side never becomes
    `condition_path` (§6.5).
15. Approve the `LogicalCell` decomposition, bbox, text, deterministic ID and
    kind rules in §5.6/§9.3, including the canonical word universe.
16. Approve strict snapshot schema validation (`table_params_snapshot_schema_invalid`,
    `table_params_snapshot_version_mismatch`) and the §13 edit boundary for
    S2b-Schema.

## 15. Acceptance checklist for the design gate

- [ ] Six deliverables are answered: data model, mapping, merged cells,
      boundary decisions, evidence chain, failure strategy.
- [ ] R1–R7 are answered with repository paths and line references.
- [ ] P0-1..P0-4 and P1-1..P1-5 are closed in the document.
- [ ] N1 is closed: `HeaderCanopyEvidence` is directed, names both anchors,
      and an independent auditor can decide the boundary from the record and
      the header cells alone.
- [ ] N2 is closed: `SubrulePromotedEvidence` carries per-band, per-cell and
      per-word assignments, and `short_label_ratio` is recomputable from them.
- [ ] N3 is closed: `TableBBoxEvidence` and `RegionExtentEvidence` are checked
      against a fresh parse, and the `implied_outer` values are structurally
      encoded.
- [ ] N4 is closed: candidate grouping uses a fixed anchor and retains every
      source x.
- [ ] N5 is closed: `condition_path` requires an explicit condition marker and
      the ratio formula is exact.
- [ ] N6 is closed: `LogicalCell` bbox, text, id, row-span and word universe
      are reproducible without algorithm-specific knowledge.
- [ ] N7 is closed: `gold_annotation_state` and `gold_ambiguity_status` are
      independent axes joined by `item_id`.
- [ ] N8 is closed: v1/v2 snapshots are schema-validated, and the S2b-Schema
      edit boundary is explicit.
- [ ] S1–S3 are closed: role-ref contradiction, projection/visual geometry and
      structural/tie-break edge cases.
- [ ] Hard constraints in §4 are accepted.
- [ ] Proposed parameters and the v1/v2 snapshot dispatch are approved or
      amended.
- [ ] S2b evaluation set, ambiguity overlay, metrics and anti-overfitting rules
      are approved.
- [ ] No implementation is authorized until this design gate passes.
