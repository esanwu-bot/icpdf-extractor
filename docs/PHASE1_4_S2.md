# Phase 1.4 S2 — VisualBoundary / LogicalColumn separation and logical projection

Status: **design and data-model change proposal only**.  No implementation code
is part of this proposal.  Implementation starts only after the Reviewer
confirms this document.  S1 behaviour is frozen; `RulePrimitive`,
`RuleComponent` and `TableRegion` aggregation, Gold v2 (`gen-2026-11-06.2`)
and the Candidate Registry contract are not changed by this proposal.

S1 acceptance basis (as recorded by the Reviewer):

* S1 implementation `003311fa8ee24ef68254fa3852329a9a9f1d762a`
* S1 review fix `3fc45195d8da20d95dd30ef87ef19859d3d2e002`
* review evidence bundle `ff52189caf1a99226eacdc01e4e76cd0f2ae2ba7`

This proposal does not claim an independent source audit of S1.  The numbers in
section 2 come from a design-time probe on the frozen S1 parser and are
re-verified only when S2d is implemented.

## 1. Scope

S2 separates the two column representations Gold v2 already distinguishes and
adds the logical projection that the separation requires:

1. **Visual boundaries** — every printed vertical separator, including
   body-only condition sub-rules and partial rules.
2. **Logical columns** — the semantic columns used for header attribution and
   roles, including columns that exist only as header-canopy or label
   boundaries.
3. **Logical projection** — physical cells projected onto logical columns,
   allowing many physical cells → one logical cell and one logical cell →
   many visual columns.
4. **Section bands** — cross-column logical cells for section title rows,
   represented as logical spans without changing the physical grid.
5. **Condition bands and `condition_path`** — demoted sub-rules become
   condition attributes and context, not parameter/value columns.
6. **Fail-closed mapping** — when the logical mapping cannot be decided, the
   table reports `logical_columns = null` and
   `logical_mapping_status = unresolved`; nothing is forced.
7. **Traceability** — logical cells and candidates reference physical cell ids
   and word ids; candidates carry the logical column and context path.

Frozen constraints carried from the Reviewer instruction:

* do not change S1 RulePrimitive / RuleComponent / TableRegion behaviour;
* do not change Gold v2 annotations;
* no S3 drawing/schematic gate, no S4 general role expansion;
* no OCR, LLM or other PDF engine;
* no vendor, model or page special cases;
* do not improve LogicalColumn metrics by changing Detection results.

## 2. Why S2 is needed — measured current state

The S1 parser emits one lattice, `TableGrid.xs`, and indexes headers and roles
by that lattice's columns.  It has no visual/logical split and no row roles.
The probe below compares the frozen S1 grid with Gold v2 on the cases named in
the S2 scope.

Legend: `vis` = gold `visual_columns`; `log` = gold `logical_columns`;
`grid` = S1 `TableGrid.n_columns`; `verticals` = measured vertical x positions
and their coverage of the region height (outer edges are included where the
probe listed them).

| Item | Gold vis / status / partial | Gold log | S1 grid | Measured verticals (coverage) | Consequence |
| --- | --- | --- | --- | --- | --- |
| MICRF103-P03-T01 | 6 / implied_outer / — | 6 | 6 | 184.1, 446.9, 482.9, 518.9, 554.9 (0.881); no outer verticals | Visual boundaries add the two outer edges; row 1/9/15/19 are one logical cell spanning all 6 columns |
| CY29FCT520-P04-T01 | 4 / printed / — | 8 | 8 | 45.5, 331.9, 421.4, 511.1, 547.0 (1.0) | Four logical boundaries (362.9, 393.2, 452.6, 482.9) exist only as header-canopy boundaries; logical > visual |
| CY29FCT520-P04-T02 | 6 / partial / 173.2 | 9 | 9 | 45.5, 108.3, 173.2, 325.7, 418.4, 511.1, 547.0 | 173.2 is a 0.072-coverage body sub-rule; visual only, not logical |
| CY29FCT520-P05-T01 | 7 / partial / 193.9, 266.0 | 9 | 11 | 129.0 (1.0), 193.9 (0.556), 266.0 (0.556), 346.5 (1.0), 439.1 (1.0), 531.9 (1.0) | S1 grid wrongly keeps 193.9 and 266.0; both must be demoted (11 → 9) |
| CY29FCT520-P06-T01 | 5 / partial / 289.8 | 7 | 6 | 290.2 (0.576), 337.7 (1.0), 424.4 (1.0), 511.1 (1.0) | S1 grid wrongly drops 290.2; it must be promoted by right-side short labels (6 → 7) |
| CY29FCT520-P08-T01 | null / not_printed / — | 12 | 9 | only 36.8 and 832.7 (1.0) | No visual boundaries; S1 under-splits the header labels (known miss, not forced) |
| DS10CP152-P04-T01 | 8 / partial / 346.1 | 7 | 7 | 89.1/285.6/426.8/462.0/492.3/527.3 (0.871), 346.1 (0.108) | 346.1 is body-only; already absent from `grid.xs`; visual only |
| DS10CP152-P05-T01 | 8 / partial / 363.1 | 7 | 7 | 123.6/278.4/428.0/462.9/492.9/527.9 (0.929), 363.1 (0.422) | Same: 363.1 is body-only, visual only |
| DS10CP152-P11-T01 | null / not_printed / — | 10 | 10 | only outer edges (1.0) | Logical mapping comes from the header labels only |
| DS10CP152-P13-T02 | 2 / printed / — | 2 | 2 | fully ruled cells | `header_rows = 0`; no section or sub-rule impact |

Findings that change the earlier design assumptions:

1. **`logical_columns <= visual_columns` is false.**  Gold v2 has 8 logical /
   4 visual on CY29 P04-T01 and 9 logical / 7 visual on P05.  Header canopies
   create logical boundaries that have no printed separator.  Section 6
   replaces the old invariant in `PHASE1_4_STRUCTURE_MODEL.md` §3.3.
2. **Coverage 0.85 is the right full-height threshold.**  Full-height rules
   measure 0.871–1.000 because region bboxes extend slightly beyond the rule
   ends; body sub-rules measure 0.072–0.576.  A 0.85 threshold separates both
   groups on all probed cases.
3. **Partial rules need two outcomes, not one.**  Demotion handles CY29 P05 and
   DS10 P04/P05.  Promotion is required for CY29 P06, where the right side of
   the 0.576-coverage rule is the repeated short label `Data` / `I`.
4. **Section spans are physical, not a fixed "all columns".**  Gold gives the
   MICRF P03 section rows `column_span = 6`, but the DS10 P04/P05 section rows
   `column_span = 2`.  The difference is whether an internal vertical rule
   crosses the row band: MICRF section bands have none (full-width band);
   DS10 section rows are crossed by the internal verticals (the printed merged
   cell is bounded).
5. **S1 detection already matches the physical grid** in all probed cases;
   S2 must be a read-only projection over `grid.xs`, `grid.ys` and the cell
   bboxes.  It must not alter them.

## 3. Three lattices

| Lattice | Existing / new | Role |
| --- | --- | --- |
| Recognition / cell lattice | existing `TableGrid.xs`, `TableGrid.ys`, `GridCell` | Physical detection grid; frozen in S2 |
| Visual boundary lattice | new | Printed vertical separators, including partial ones; drives VisualBoundary metrics |
| Logical boundary lattice | new | Semantic column boundaries; drives header attribution, roles and logical exactness |

The visual lattice is derived from the region's ruled components.  The logical
lattice starts from `grid.xs` and applies the demotion/promotion decisions
below.  Neither lattice modifies the recognition lattice.

## 4. Visual boundaries

### 4.1 Derivation

For an accepted `TableRegion`:

1. Collect every vertical `RuleSegment` from the region's components with
   `length >= 4pt` and x within 2.5pt of the region's x-range.  Internal
   positions are strictly inside; the edge positions (within 2.5pt of
   `bbox.x0/x1`) are measured separately to decide whether an outer edge is
   drawn.
2. Merge collinear segments at the same x and compute
   `coverage = union_length / region_height` clipped to the region.
3. `partial_boundaries` are internal x positions with `coverage < 0.85`.
4. `visual_boundaries` = sorted outer edges (`bbox.x0`, `bbox.x1`) plus every
   internal x.  Outer edges are always present, whether drawn or implied.
5. `visual_columns = len(visual_boundaries) - 1` when at least one internal
   separator exists, otherwise `null`.

### 4.2 Status

| Condition | `visual_boundary_status` |
| --- | --- |
| no internal vertical separator | `not_printed` |
| at least one internal separator with `coverage < 0.85` | `partial` |
| internal separators exist, both outer edges are not drawn | `implied_outer` |
| internal separators exist, both outer edges drawn | `printed` |

An outer edge is **drawn** when a vertical segment at that x has coverage
`>= 0.85`; otherwise it is implied by the horizontal-rule extent.  Example
check: MICRF P03 has five internal verticals at 0.881 coverage and no outer
verticals → `implied_outer`, 6 columns.  DS10 P04 has six full-height
verticals plus 346.1 at 0.108 → `partial`, 8 columns.

## 5. Logical boundaries

### 5.1 Base and classification

The logical lattice starts as `grid.xs` (the recognition lattice) and applies
one decision per internal boundary:

| Evidence | Decision | `logical_boundary_source` |
| --- | --- | --- |
| full-height visual separator (`coverage >= 0.85`) | keep | `printed_rule` |
| no visual separator, aligned with a header-canopy boundary | keep | `header_canopy` |
| no visual separator, aligned with a stable label run | keep | `label_aligned` |
| full-height separator that does not split any populated cell | keep | `structural` |
| partial separator (`coverage < 0.85`) | demote by default | `subrule_demoted` |
| partial separator promoted by right-side short labels | keep | `subrule_promoted` |

The header/label evidence for boundaries absent from `grid.xs` uses the
existing header cells and word runs; no new text extraction is introduced.

### 5.2 Sub-rule promotion rule

A partial separator may be promoted to a logical boundary only when the label
evidence is explicit.  For every row band the rule intersects:

1. find the nearest word run immediately to the right of the separator,
   inside the same physical cell;
2. classify the run as a **short label** when it has:
   * at most 2 words and at most 12 characters,
   * at least one letter,
   * no digit,
   * is not a unit-only token (`V`, `A`, `mA`, `µA`, `ns`, `MHz`, `kΩ`, …);
3. promote when short labels occur in at least 50% of the non-empty bands and
   in at least 2 bands.

Measured cases:

* CY29 P06 `290.2` (coverage 0.576): right-side runs are `Data` / `I` in 4 of
  5 bands → promote; 6 → 7 logical columns.
* CY29 P05 `193.9`, `266.0`: right side is condition prose
  (`VCC = 5.5 V, Outputs open, …`) → demote.
* DS10 P04 `346.1`, P05 `363.1`: right side is numeric / unit content → demote.

If short labels occur in at least 2 bands but the ratio is in
`[0.25, 0.5)` — evidence exists but does not meet the promotion threshold —
the boundary is **mixed**: it is **unresolved** and the table fails closed
(§8) rather than choosing a side.  A ratio below 0.25 is a plain demotion.

### 5.3 Logical column count and role of a promoted split

`logical_boundaries` are the kept x positions with the two outer edges;
`logical_columns = len(logical_boundaries) - 1` when the mapping is decided.

A promoted partial split creates a condition sub-column.  Its role is
`condition` with `role_source = "subrule_short_label"`.  The left part keeps
whatever role its header provides, otherwise `unknown`.  No role is inferred
from mere adjacency.  This deliberately narrows the Gold-spec example
"an unlabeled column left of MIN/TYP/MAX is a condition column": in CY29 P06
the left parameter column must stay `unknown`, while the promoted sub-column is
`condition`.  See open question 4.

## 6. Invariants

These replace the old `logical_columns <= visual_columns` invariant:

1. `visual_columns` is `null` exactly when `visual_boundary_status` is
   `not_printed`.
2. When visual boundaries exist, every logical boundary is either within 2.5pt
   of a visual boundary or has header/label evidence.  No logical boundary is
   invented from cell content alone.
3. When visual boundaries exist, every visual column interval overlaps at least
   one logical column and every logical column overlaps at least one visual
   column.  A visual column may overlap several logical columns (header
   canopy); several visual columns may map to one logical column (demoted
   sub-rule).
4. If `logical_mapping_status = unresolved`, then `logical_columns` is `null`,
   `logical_boundaries`, `column_projection`, `logical_cells`,
   `logical_headers` and `logical_column_roles` are empty; visual fields and
   physical detection are still emitted.
5. No logical field may change `grid.xs`, `grid.ys`, cell bboxes/text or the
   region aggregation.

## 7. Logical projection, section bands and condition bands

### 7.1 Projection

`ColumnMapping` is overlap-based, not a partition:

```text
ColumnMapping
  logical_column: int
  visual_columns: tuple[int, ...]      # visual intervals it overlaps
  left, right: float                   # logical interval
  evidence: tuple[str, ...]            # printed_rule | header_canopy | ...
```

Consequences:

* one visual column may appear in several logical mappings (CY29 P04-T01
  visual column 1 contains logical MIN/NOM/MAX);
* one logical column may contain several visual columns (CY29 P05 visual
  columns 1–3 are one condition column, logical column 1).

### 7.2 Logical cells

For each physical row and logical column:

* find the physical `GridCell`s whose bbox intersects the logical interval;
* assign each word by its center to exactly one logical column, so a cell that
  straddles a promoted boundary is split at word level without duplication;
* if several physical cells fall in the same logical column, emit one logical
  cell whose `physical_cell_ids` lists all of them and whose text is their
  reading-order concatenation;
* `word_ids` records every contributing `TextWord.word_id`.

`LogicalCell`:

```text
LogicalCell
  logical_cell_id: str                 # deterministic, content-independent
  row_start, row_end: int              # inclusive physical grid rows
  logical_column, logical_column_span: int
  bbox
  text
  kind: data | header | section | condition
  physical_cell_refs: tuple[PhysicalCellRef, ...]   # parser level
  physical_cell_ids: tuple[str, ...]                # domain level, resolved
  word_ids: tuple[str, ...]
```

`DetectedCell` has no id in S1; domain ids are generated in
`table_rebuilder.build_table`.  The parser therefore refers to a physical cell
by position:

```text
PhysicalCellRef
  grid_row: int        # GridCell.row
  cell_index: int      # index inside DetectedRow.cells
  column_index: int    # DetectedCell.column_index, for readability
```

`build_table` resolves `(grid_row, cell_index) -> cell_id` while it creates
the domain cells and copies the resolved ids into `physical_cell_ids` /
`source_cell_ids`.  Existing cell-id generation, including the ragged-row
column shift, is unchanged.  Header references are resolved in the same place
from the existing `HeaderCell` ids.

The physical `DetectedCell` additionally carries `logical_column`,
`logical_cell_id` and `word_ids`; its text, bbox and column index are
unchanged.

### 7.3 Section bands

Detection (all must hold):

1. the row is not a header row;
2. exactly one populated physical cell in the row;
3. that cell starts at visual column 0 or has `column_span >= 2`;
4. the bold ratio of the cell text — characters in spans with `flags & 16`
   (or a bold font name) divided by all characters — is at least 0.90;
5. the text contains a letter and is not numeric/unit-only.

A span is assigned to a physical cell when its bbox center lies inside the
cell bbox; the bold ratio is the character count of assigned spans with bold
flags divided by the character count of all assigned spans.  A cell with no
assigned span text has ratio 0 and cannot be a section.

`merged column_span >= 2` is corroborating evidence, not a substitute for the
bold test.  A bold numeric row and a bold multi-cell data row are rejected
because of rules 2 and 5.  Measured: MICRF P03 rows 1/9/15/19 and DS10 P04/P05
section rows pass; the bold numeric cells in MICRF data rows (for example
`26.5`, `27.5`) are rejected because the row has several populated cells.

Logical span:

* collect the internal visual boundaries whose vertical segments intersect the
  row band;
* **no crossing boundary** → the band is full-width; the logical cell spans all
  logical columns (MICRF P03: `column_span = 6`, bbox = table width);
* **crossing boundaries exist** → the band is bounded; the logical cell spans
  exactly the logical columns covered by the label cell
  (DS10 P04/P05: `column_span = 2`).

`SectionBand`:

```text
SectionBand
  band_id, row_start, row_end
  text, bbox
  visual_columns: tuple[int, ...]
  logical_columns: tuple[int, ...]
  source_cell_refs: tuple[PhysicalCellRef, ...]     # parser level
  source_cell_ids: tuple[str, ...]                  # domain level, resolved
  bold_ratio: float
  crossing_boundaries: tuple[float, ...]
  evidence: tuple[str, ...]
```

Section rows stay in `rows`; they are not deleted and do not change
`reconstruction_status` (see open question 8).  The section label becomes a
`SECTION` candidate, not a parameter/value candidate.  The same physical cell
yields the same `candidate_id`, so candidate count and ids stay stable.

### 7.4 Condition bands and `condition_path`

Demoted partial separators become `ConditionBand`s.  Contiguous demoted
separators inside one logical column and overlapping row ranges are grouped
into one band:

```text
ConditionBand
  band_id, row_start, row_end, bbox
  boundary_x: tuple[float, ...]        # demoted separators
  visual_columns: tuple[int, ...]
  logical_columns: tuple[int, ...]     # usually one covering logical column
  source_cell_refs: tuple[PhysicalCellRef, ...]     # parser level
  source_cell_ids: tuple[str, ...]                  # domain level, resolved
  label: str | None                    # header path only; never invented
  demotion_reason: str
```

`ContextRef` preserves the hierarchy:

```text
ContextRef
  kind: section | condition
  band_id
  label
  source_cell_id
  source_row
```

* `DetectedRow.context_refs` (and domain `TableRow.context_refs`) lists
  section refs applying to that row (a new section closes the previous one);
* a candidate's `context_path` = row section refs + condition refs whose row
  range contains the cell and whose logical column contains the candidate's
  logical column;
* a `ConditionBand` label is the covering logical column's header path when
  available (for example `TEST CONDITIONS`), otherwise empty; per-row varying
  condition text is a condition-column value, not a context label.

This keeps section/condition hierarchy out of ordinary parameter and value
columns without inventing labels.

### 7.5 Logical headers and roles

`logical_headers`, `logical_header_path` and `logical_header_cells` are built by
overlapping the existing header cells with logical intervals.  The parser
emits `LogicalHeaderRef {level, source_column, logical_column, text, bbox}`;
`table_rebuilder` turns each ref into a domain `HeaderCell` whose
`column_id` is the logical column and whose `source_cell_id` is the resolved
physical cell (new id shape `{table_id}-lh{level:02d}-c{logical_column:02d}`,
leaving S1 header ids untouched).

* a canopy cell backs every logical column it overlaps;
* sub-labels (`MIN`, `TYP`, `MAX`) are appended in header-level order;
* an empty printed header stays empty and its role is `unknown`;
* an unlabelled logical column that is not created by a promoted sub-rule is
  `unknown`.

`logical_column_roles` uses the existing `role_for_header` mapper.  Role
sources: `header_text`, `subrule_short_label`, `fail_closed`.  The physical
`headers` and `column_roles` fields stay as they are in S1; the logical fields
are additive (see open question 9).

## 8. Fail-closed behaviour

The logical mapping is `unresolved` when any of the following holds:

* a partial separator has mixed short-label evidence below the promotion
  threshold;
* header-canopy boundaries conflict with printed boundaries and cannot be
  ordered;
* `not_printed` tables have no stable header/label boundaries;
* when visual boundaries exist, a logical interval has no visual overlap or a
  visual interval has no logical overlap;
* word-center assignment is ambiguous at a promoted boundary.

On `unresolved`:

* `logical_columns = null`, `logical_mapping_status = "unresolved"`;
* no logical cells, headers, roles or projection;
* the table is still detected; visual fields, rows, cells and physical
  candidates are emitted exactly as in S1 (candidate logical fields are null);
* the table stays in the logical exactness denominator as a miss, and is
  reported as `logical_mapping_unresolved`; it is not silently excluded.

## 9. Proposed data-model changes

All changes are additive with defaults.  No existing field is renamed,
removed or reinterpreted.  `extra="forbid"` models remain valid for old JSON.

### 9.1 New modules

`src/icpdf/domain/logical.py` (new; shared, serializable models so the domain
layer does not import the parser):

* `BoundaryEvidence`, `VisualBoundary`, `LogicalBoundary`, `ColumnMapping`
* `PhysicalCellRef`, `LogicalHeaderRef`, `SectionBand`, `ConditionBand`,
  `ContextRef`, `LogicalCell`
* `LogicalStructure` (the complete visual + logical result for one region)

`src/icpdf/parser/logical_structure.py` (new; no changes to
`rule_primitives.py`, `table_regions.py` or `structure.py`):

* `build_logical_structure(layout, region, grid, semantics, params)`, returning
  a `LogicalStructure` whose physical references are `PhysicalCellRef`s.

The parser module consumes S1 outputs read-only.  It is the only place where
the demotion, promotion and projection rules live.  `table_rebuilder` resolves
refs to domain cell ids; no domain module imports the parser.

### 9.2 Additive fields

| Model | New fields (default) |
| --- | --- |
| `TextSpan` (`text_blocks.py`) | `flags: int \| None = None` — exposes PyMuPDF bold bit 16; font-name parsing remains a fallback |
| `DetectedTable` | `visual_boundaries: tuple[float, ...] = ()`, `visual_boundary_status: str = "unknown"`, `visual_columns: int \| None = None`, `partial_boundaries: tuple[float, ...] = ()`, `logical_boundaries: tuple[float, ...] = ()`, `logical_columns: int \| None = None`, `logical_mapping_status: str = "unresolved"`, `column_projection`, `section_bands`, `condition_bands`, `logical_cells`, `logical_headers`, `logical_header_path`, `logical_header_cells`, `logical_column_roles` |
| `DetectedCell` | `logical_column: int \| None = None`, `logical_cell_id: str \| None = None`, `word_ids: tuple[str, ...] = ()` |
| `DetectedRow` | `row_role: str = "data"`, `context_refs: tuple[ContextRef, ...] = ()` (it already has `grid_row`) |
| domain `Table` | the same logical/visual fields, as lists; `logical_header_cells: list[HeaderCell]` (logical `column_id`), and resolved `physical_cell_ids` / `source_cell_ids` |
| domain `Cell` | `logical_column: int \| None = None`, `logical_cell_id: str \| None = None`, `word_ids: list[str] = []` |
| domain `TableRow` | `grid_row: int \| None = None`, `row_role: str = "data"`, `context_refs: list[ContextRef] = []` |
| `Candidate` | `logical_column: int \| None = None`, `logical_cell_id: str \| None = None`, `context_path: list[ContextRef] = []`; `CandidateType` gains `SECTION = "section"` |
| `Candidate` roles | section rows use `candidate_type=SECTION`, `column_role=UNKNOWN`, `role_source="section_band"`; other candidates use the logical column role |
| `TableParams` | additive defaults only: `subrule_logical_span=0.85`, `section_bold_ratio=0.9`, `short_label_max_words=2`, `short_label_max_chars=12`, `short_label_band_ratio=0.5`, `visual_min_rule_span_pt=4.0` |

`TableParams` values live in code defaults; the YAML config and its SHA
`ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c` stay
unchanged.

### 9.3 Candidate and evidence traceability

When the mapping is decided, `build_candidates` looks up the role and header
through `cell.logical_column` in `logical_column_roles` / `logical_headers`;
when the mapping is unresolved it falls back to the S1 physical
`headers` / `column_roles`.  Candidate ids, cell ids, bboxes, raw text and
unit extraction are unchanged.

* `candidate_id` remains `"{document_id}:{cell_id}"`; ids and bboxes are
  unchanged.
* Every candidate gains `logical_column`, `logical_cell_id` and
  `context_path` when the mapping is decided.
* Every `LogicalCell` lists `physical_cell_refs` at parser level and
  `physical_cell_ids` in the domain table, plus `word_ids`.
* Every `VisualBoundary` / `LogicalBoundary` records its source evidence
  (rule component ids / header cell ids) and coverage.
* Section and condition bands record `source_cell_refs`, resolved to
  `source_cell_ids` in the domain table.
* When the mapping is unresolved, candidate logical fields stay null; no
  physical candidate is dropped.

### 9.4 Example records

MICRF103 P03 section row (gold form: one cell, `column_span = 6`):

```yaml
section_bands:
  - band_id: p3-r1-s1
    row_start: 1
    row_end: 1
    text: Power Supply
    visual_columns: [0, 1, 2, 3, 4, 5]
    logical_columns: [0, 1, 2, 3, 4, 5]
    source_cell_refs: [{grid_row: 1, cell_index: 0, column_index: 0}]
    bold_ratio: 1.0
    crossing_boundaries: []
logical_cells:
  - logical_cell_id: p3-r1-lc0-ls6
    row_start: 1
    row_end: 1
    logical_column: 0
    logical_column_span: 6
    bbox: [46.8, 202.8, 586.8, 219.1]
    text: Power Supply
    kind: section
    physical_cell_refs: [{grid_row: 1, cell_index: 0, column_index: 0}]
```

The domain table replaces `source_cell_refs` / `physical_cell_refs` with the
resolved `source_cell_ids` / `physical_cell_ids` (for example
`p003-t01-r02-c00`), so candidates and evidence point at real domain cells.

DS10CP152 P04 section row (gold form: one cell, `column_span = 2`):

```yaml
section_bands:
  - band_id: p4-r1-s1
    row_start: 1
    row_end: 1
    text: LVCMOS DC SPECIFICATIONS
    visual_columns: [0, 1]
    logical_columns: [0, 1]
    source_cell_refs: [{grid_row: 1, cell_index: 0, column_index: 0}]
    bold_ratio: 1.0
    crossing_boundaries: [89.1, 285.6, 426.8, 462.0, 492.3, 527.3]
```

CY29 P05 demoted condition band:

```yaml
condition_bands:
  - band_id: p5-r4-b1
    row_start: 4
    row_end: 11
    boundary_x: [193.9, 266.0]
    visual_columns: [1, 2, 3]
    logical_columns: [1]
    label: TEST CONDITIONS
    demotion_reason: subrule_coverage_below_threshold
```

## 10. Evaluation changes

The evaluator already reports `visual_column_count_exact` and
`logical_column_count_exact`, but both currently use the single physical
`pred_columns` (`tools/goldset/evaluate.py`).  S2 adds independent predicted
values:

* `pred_visual_columns` from `DetectedTable.visual_columns`;
* `pred_logical_columns` from `DetectedTable.logical_columns`;
* `pred_visual_status` and `pred_logical_status`;
* legacy `pred_columns` stays the S1 physical count and is reported separately.

| Metric | Numerator | Denominator | Exclusion |
| --- | --- | --- | --- |
| Visual boundary exactness | `pred_visual_columns == gold.visual_columns` | gold status `printed` / `partial` / `implied_outer` (19 of 21) | `not_printed` (`visual_column_excluded_not_printed`) |
| Logical column exactness | `pred_logical_columns == gold.logical_columns` | gold `logical_columns` is not null (21) | gold undecided only (`logical_column_excluded_undecided`) |
| Header attribution | labelled logical columns with matching header path | labelled logical columns in tables with `pred_logical_columns == gold.logical_columns` and a decided mapping | unmapped logical columns (`header_unmapped_columns`) |
| Role accuracy | logical columns with matching role | mapped logical columns in the same comparable tables | unmappable logical columns (`role_unmapped_columns`) |
| Physical column count | `pred_columns == gold.n_columns` | all matched tables | none; must be item-by-item identical to S1 |

A predicted `unresolved` table remains in the logical denominator as a miss.
It is not excluded, because the denominator is defined by the gold mapping.
Detection, row count and cell-text metrics continue to include every accepted
table.

Design-time expectation (not an acceptance claim): visual 19/19 and logical
20/21, with CY29 P08 as the known miss.  S2d re-runs the frozen sets and
reports both plus the legacy physical line; any difference from this
expectation must be explained per item.

Regression proof for the frozen sets (Phase 1.2 46 tables and Gold v2 21
tables):

* per-item diff of `bbox`, row count, row bboxes, cell ids/bboxes/text,
  `detection_method`, `region_components`, `boundary_source`,
  `reconstruction_status` is empty;
* per-item diff of `candidate_id`, `cell_id`, `bbox`, `raw_text` is empty;
* `column_role` / `candidate_type` changes are allowed only where the logical
  mapping differs and are listed per item;
* no metric is packaged as an acceptance version until the Reviewer confirms
  the rerun report.

## 11. Evidence Validator additions

New reference-integrity checks (structural only, **not semantic proof**):

1. `visual_boundary_status` in the four-value vocabulary; `not_printed` implies
   `visual_columns == null` and no partial boundaries; otherwise
   `visual_columns == len(visual_boundaries) - 1`.
2. Visual bounds sorted, inside the table bbox, outer edges within 2.5pt of
   `bbox.x0/x1`; partial boundaries are a subset of visual boundaries.
3. `logical_mapping_status` in `decided | unresolved`; when decided,
   `logical_columns == len(logical_boundaries) - 1`, bounds sorted and inside
   the table bbox, projection covers every logical column, and
   `logical_headers` / `logical_column_roles` lengths match; when unresolved,
   all logical payloads are empty and `logical_columns` is null.
4. Projection: logical indices contiguous from 0; visual indices valid; when
   visual boundaries exist, every visual column is overlapped by at least one
   logical column; no projection interval falls outside the table.
5. Section/condition bands: row ranges inside `[0, n_rows)`, not inside the
   header band for sections, source cell ids exist, visual/logical column
   indices valid, `bold_ratio` in `[0, 1]`.
6. `grid_row` values are unique and non-negative; `row_role` is in the fixed
   vocabulary; every context `band_id` resolves to a section or condition
   band, and a section ref's row is inside that band.
7. Logical cells: physical cell ids exist (domain) and every parser-level
   ref resolved to exactly one emitted cell, word ids unique, logical column
   valid, section cells cover their band's logical columns.
8. Candidates: logical column/cell references resolve; section candidates have
   `candidate_type=SECTION` and a section `source_cell_id`; unresolved tables
   carry no logical references.

Every code above gets a positive and a corrupted-negative fixture.  Passing
the validator is still not evidence that a boundary is semantically correct;
metrics and per-item review remain the semantic gate.

## 12. Test plan

### 12.1 Synthetic unit tests (new `tests/unit/test_logical_structure.py`)

Positive:

1. Bold solo full-width section row → one logical cell spanning all columns.
2. Bold merged two-column section row with crossing rules → span 2.
3. Header canopy splits one visual column into MIN/TYP/MAX logical columns.
4. Demoted sub-rule merges two visual intervals into one logical column.
5. Promoted sub-rule with repeated short labels → one extra condition column.
6. Two physical cells projected into one logical cell (physical ids both
   listed).
7. One logical cell spanning several visual columns (section band).
8. `not_printed` table with stable header labels → decided mapping.
9. Cell straddling a promoted boundary → word-center split, no duplication.
10. Section followed by data rows → `row_context` closes at the next section.

Negative:

11. Bold numeric full-width row → not a section.
12. Bold multi-cell data row → not a section.
13. Header row with bold styling → not a section.
14. Sub-rule with prose right side → demoted.
15. Sub-rule with numeric/unit right side → demoted.
16. Sub-rule with mixed label/prose evidence → `unresolved`.
17. `not_printed` table without stable labels → `unresolved`.
18. Whole-table bold with no solo rows → no section, mapping intact.

### 12.2 Real PDF integration tests

`tests/integration/test_phase14_s2.py` (skips when PDFs are absent):

* MICRF103 P03: physical 30×6 unchanged; visual 6 / implied_outer; logical 6;
  section bands rows 1/9/15/19 span 6.
* CY29 P04-T01: visual 4 / printed; logical 8.
* CY29 P04-T02: visual 6 / partial [173.2]; logical 9.
* CY29 P05: visual 7 / partial [193.9, 266.0]; logical 9 with both demoted.
* CY29 P06: visual 5 / partial [289.8]; logical 7 with 290.2 promoted and the
  split column role `condition`.
* CY29 P08: visual null / not_printed; logical mapping reported as 9 (known
  miss vs gold 12), not forced to 12.
* DS10 P04/P05: visual 8 / partial [346.1] / [363.1]; logical 7.
* DS10 P11: visual null / not_printed; logical 10.
* DS10 P13-T02: `header_rows = 0`; visual 2 / printed; logical 2.
* All 46 Phase 1.2 + 21 Gold v2 items: physical per-item diff empty.
* `tools/validate_evidence --strict`: 0 errors, 0 warnings on the frozen runs.

### 12.3 Unit-level regression

* `TableGrid.xs`, `ys`, cells and region aggregation snapshots unchanged for
  the frozen cases.
* `DetectedTable` serialization round-trips with default logical fields, so S1
  JSON remains readable.

## 13. Implementation slices after approval

| Slice | Content | Acceptance |
| --- | --- | --- |
| S2a | new `logical_structure.py`; additive models; visual boundaries and status | visual 19/19 on the gold comparable set; physical diff empty |
| S2b | logical boundaries, demotion/promotion, projection, logical headers/roles, fail-closed | logical 20/21; no physical change; unresolved tables keep physical payload |
| S2c | section/condition bands, `context_path`, candidate tagging | MICRF section rows span 6, DS10 span 2; section candidates; candidate ids unchanged |
| S2d | evaluator visual/logical split, validator codes, frozen reruns and report | separate metrics; validator 0/0; per-item physical diff empty |

Each slice is a separate local commit with its full SHA in the report.  No push
to Codeup.  No slice is reported as accepted before Reviewer confirmation.

## 14. Open questions for the Reviewer

1. **Section evidence.**  Is requiring bold (≥90%) plus a solo populated cell
   acceptable, with a merged span only corroborating?  Should an unbolded
   merged section row be an `unresolved` section candidate instead of a
   section, or silently remain a data row?
2. **Invariant correction.**  Approve replacing
   `logical_columns <= visual_columns` with the evidence-based invariants in
   section 6.  Gold v2 already contradicts the old invariant (CY29 P04-T01
   8/4, P05 9/7).
3. **Section span.**  Approve the crossing-rule test (no crossing → full
   width; crossing → label cell span).  It reproduces MICRF `column_span = 6`
   and DS10 `column_span = 2` from the page's own ruling.
4. **Promoted sub-column role.**  Approve `condition` with
   `role_source = subrule_short_label` and no adjacency-only inference.  This
   narrows the Gold-spec example: CY29 P06's left parameter column stays
   `unknown`.
5. **Fail-closed granularity.**  Approve table-level `logical_columns = null`
   when any boundary is unresolved, rather than a partially mapped table.
6. **Promotion thresholds.**  Approve `subrule_logical_span = 0.85`,
   `short_label_max_words = 2`, `short_label_max_chars = 12`,
   `short_label_band_ratio = 0.5` and the unit-only exclusion.  These are
   measured on five documents only, not tuned on the gold answers.
7. **CY29 P08.**  Accept the known 9-vs-12 logical undercount as a reported
   miss in S2 and defer header-label column splitting (a candidate for S4), or
   require label-run splitting in S2?
8. **Section rows and status.**  Keep section rows in `rows` and leave
   `_ragged_rows` / `reconstruction_status` unchanged (probed statuses do not
   change either way), or exclude section rows from the ragged expectation?
9. **Field migration.**  Keep physical `headers` / `column_roles` and add
   `logical_*` fields, or migrate the existing fields to logical semantics in
   a later slice?  This proposal keeps both to avoid changing S1 consumers.
10. **Section candidates.**  Approve `CandidateType.SECTION` with the same
    `candidate_id` as the physical cell, replacing the value/row-label
    candidate for section rows (candidate count unchanged).
11. **TextSpan flags.**  Approve adding `TextSpan.flags` so bold detection has
    a stable source instead of font-name parsing alone.
12. **Partial condition band.**  Emit the richer `ConditionBand` only, or also
    a Gold-spec-shaped `partial_condition_band` field?  Gold v2 currently has
    no instances, so there is no annotation to validate the latter.

## 15. Non-goals

No S3 drawing/schematic gate; no S4 role expansion; no OCR/LLM/other engine;
no vendor/model/page special case; no Gold v2 edit; no detection or
`RuleComponent`/`TableRegion` change; no YAML config change; no Codeup push;
no acceptance version built from unreviewed metrics.
