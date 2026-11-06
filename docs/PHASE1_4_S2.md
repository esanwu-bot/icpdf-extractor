# Phase 1.4 S2 — VisualBoundary / LogicalColumn separation and logical projection

Status: **design revision r1 (post-review), data-model proposal only**.  No
implementation code is part of this proposal.  The Reviewer approved the S2
architecture direction, the three-lattice separation, the visual/logical metric
split and table-level fail-closed, but withheld S2a authorisation until the
three P0 data-model corrections (many-to-many cell mapping, header provenance,
row-index contract) and the `ConditionContext` separation in this revision are
confirmed.  S2a starts only after that confirmation.  S1 behaviour is frozen;
`RulePrimitive`, `RuleComponent` and `TableRegion` aggregation, Gold v2
(`gen-2026-11-06.2`) and the Candidate Registry contract are not changed by
this proposal.

Revision record:

* r0 `cfcaa828b33727126d27db823a65c55e58f28ef7` — initial design; reviewed.
* r1 — this document.  Incorporates the review: P0-1 many-to-many
  physical↔logical mapping, P0-2 complete header provenance, P0-3 row-index
  contract, `ConditionBand` / `ConditionContext` separation, the 12 recorded
  decisions (§14) and the frozen acceptance red lines (§16).  No PDF rerun and
  no Gold change were needed for this revision.

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
7. **Traceability** — logical cells reference the physical cells and words that
   produce them.  The physical↔logical cell relation is many-to-many and is
   stored on the logical side; candidates keep their physical identity and
   carry logical cell references plus an explicit context path.

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
`condition`.  See §14 decision 4.

## 6. Invariants

These replace the old `logical_columns <= visual_columns` invariant (withdrawn;
Gold v2 has 8 logical / 4 visual on CY29FCT520-P04-T01 and 9 / 7 on P05):

1. `visual_columns` is `null` exactly when `visual_boundary_status` is
   `not_printed`.
2. **Every logical boundary carries at least one evidence source.**  Allowed
   sources: `printed_rule`, `header_canopy`, `label_aligned`, `structural`,
   `subrule_promoted`.  A logical boundary is never created because of a
   target column count, a gold value, or cell content alone.
3. When visual boundaries exist, every logical boundary is within 2.5pt of a
   visual boundary or has header/label evidence.
4. When visual boundaries exist, every visual column interval overlaps at least
   one logical column and every logical column overlaps at least one visual
   column.  A visual column may overlap several logical columns (header
   canopy); several visual columns may map to one logical column (demoted
   sub-rule).
5. **The physical↔logical cell relation is many-to-many.**  A physical cell may
   back several logical cells and a logical cell may merge several physical
   cells; `LogicalCell.physical_cell_refs` is the authoritative reverse map.
   Word ownership is a partition: every word belongs to exactly one logical
   cell, and the word sets of logical cells sharing a physical cell are
   disjoint.
6. If `logical_mapping_status = unresolved`, then `logical_columns` is `null`,
   `logical_boundaries`, `column_projection`, `logical_cells`,
   `logical_headers` and `logical_column_roles` are empty; visual fields and
   physical detection are still emitted.
7. No logical field may change `grid.xs`, `grid.ys`, cell bboxes/text or the
   region aggregation.

## 7. Logical projection, section bands and condition context

### 7.0 Row index contract

Every row reference in this proposal uses the **zero-based physical grid row
index** (`GridCell.row`, copied to `DetectedRow.grid_row` and domain
`TableRow.grid_row`):

* `row_start` and `row_end` are **inclusive**;
* every `row_start`, `row_end` and `source_row` field and every validator range
  check uses this index;
* a `DetectedRow` array position is never used as a row reference; if an array
  position is ever needed it is named `row_index` and is not part of S2;
* rows are contiguous in S2.  Detection emits rows from `grid.ys` without
  skipping empty visual rows, and no S2 structure renumbers or compacts rows;
* `LogicalCell.row_start == row_end` for a single-row cell; a cell spanning
  several physical rows uses an inclusive range over the same index;
* the validator form is `0 <= row_start <= row_end <= n_rows - 1`.

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

The physical↔logical cell relation is many-to-many and is stored on the
logical side:

* one physical cell may be split across several logical cells when it
  straddles a promoted boundary; each word is assigned to exactly one of them;
* several physical cells may be merged into one logical cell (demoted
  sub-rule);
* therefore neither `DetectedCell` nor domain `Cell` has a single-valued
  `logical_cell_id` or `logical_column`.

`LogicalCell.physical_cell_refs` / `physical_cell_ids` is the authoritative
reverse mapping.  For physical-side queries the parser and domain cell carry
derived, possibly multi-valued caches `logical_cell_ids: tuple[str, ...]` and
`logical_columns: tuple[int, ...]`; these are projections, never the source of
truth.  A cell split by a promoted boundary has two ids in `logical_cell_ids`
and disjoint word sets.  Its text, bbox and column index are unchanged.

`logical_cell_id` is deterministic and content-independent:
`{region_id}-r{row_start:02d}[-r{row_end:02d}]-lc{logical_column:02d}` with the
`-ls{span}` suffix when `logical_column_span > 1`.  Splitting or merging
physical cells never creates, removes or renumbers a candidate id.

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
because of rules 2 and 5.  Measured: MICRF P03 grid rows 1/9/15/19 and DS10
P04/P05 section rows pass; the bold numeric cells in MICRF data rows (for
example `26.5`, `27.5`) are rejected because the row has several populated
cells.

These five conditions are a high-confidence rule, not a definition of section.
A row that is section-like but fails them — merged solo cell without bold,
unknown bold flags without a bold font name, or styling conveyed by background
fill, border or size — becomes `row_role = "unresolved_section_hint"`: a
diagnostic record only, not a `SectionBand` and not a SECTION candidate.  Its
physical candidates are emitted with `eligible_for_parameter_extraction =
false` and `eligible_for_context = true`, so a suspected title is never forced
into parameter output and never silently reinterpreted as a parameter row.
Background-fill and border-based section detection are out of scope for S2;
ordinary rows stay `data`.

Logical span:

* collect the internal visual boundaries whose vertical segments **cross** the
  row band.  A rule crosses the band when the length of its bbox clipped to the
  band's vertical interval is greater than `crossing_epsilon_pt` (default
  0.5pt).  Endpoint proximity to the band bbox is not evidence;
* if the section-like row has more than one populated cell, the single-label
  rule does not apply and the row becomes `unresolved_section_hint`; no
  `SectionBand` is emitted;
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
`reconstruction_status` (see §14 decision 8).  The row gains
`row_role = "section"` and the section's `ContextRef`; `row_role` never feeds
`_ragged_rows`.  A row with one cell may be a section or a ragged data row, and
section recognition does not alter the physical reconstruction state.

The section label becomes a `SECTION` candidate, not a parameter/value
candidate.  The same physical cell yields the same `candidate_id`, so candidate
count and ids stay stable.  Section candidates are context evidence only:
`eligible_for_parameter_extraction = false`, `eligible_for_context = true`
(§14 decision 10).

### 7.4 Condition bands and condition context

A `ConditionBand` is a **physical evidence region**: the row range and cells
spanned by one or more demoted separators.  It is not itself an inheritance
rule.  Contiguous demoted separators inside one logical column and overlapping
row ranges are grouped into one band.

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

`ConditionContext` is the separate **candidate-level relation** that inherits a
band's condition:

```text
ConditionContext
  context_id: str
  condition_band_id: str
  target_candidate_ids: tuple[str, ...]
  association_evidence: tuple[str, ...]
      # row_overlap | header_path | column_map | explicit_subrule_label
```

An association is created only from explicit evidence:

* `row_overlap` — the candidate's grid row is inside the band's inclusive row
  range **and** the band's demoted separators lie inside or immediately left of
  the candidate's physical cell on that row.  Same-row membership alone is not
  sufficient when the band and the candidate occupy unrelated column ranges;
* `header_path` — the band's label is a header path that also covers the
  candidate's logical column;
* `column_map` — the band's logical column maps to the candidate's logical
  column through `ColumnMapping`;
* `explicit_subrule_label` — the demoted separator carries a repeated short
  label that names the condition field.

If no evidence applies, no context is attached.  Several condition fields in
one row produce several context refs, one per band, in left-to-right band
order; they are never merged into one label.

`ContextRef` is the serialized path element:

```text
ContextRef
  kind: section | condition
  band_id
  label
  source_cell_id
  source_row
  evidence: tuple[str, ...]
```

* `DetectedRow.context_refs` (and domain `TableRow.context_refs`) lists the
  section refs applying to that row; a new section closes the previous one;
* a condition ref reaches a candidate only through a `ConditionContext`; a
  candidate's `context_path` = its row's section refs followed by its linked
  condition refs, ordered by `row_start` then band position;
* a `ConditionBand` label is the covering logical column's header path when
  available (for example `TEST CONDITIONS`), otherwise empty; per-row varying
  condition text is a condition-column value, not a context label.

This keeps section/condition hierarchy out of parameter/value columns, and
prevents the unconditional same-row inheritance that a single `ContextRef`
model would imply.

### 7.5 Logical headers and roles

`logical_headers`, `logical_header_path` and `logical_header_cells` are built by
overlapping the existing header cells with logical intervals.  A canopy header
may cover several logical columns, one logical header may concatenate several
physical header cells, and one physical header cell may support several logical
headers; therefore the parser emits a ref that keeps all provenance:

```text
LogicalHeaderRef
  logical_header_id: str            # deterministic
  level: int
  logical_column: int
  text: str
  bbox
  source_header_cell_refs: tuple[HeaderCellRef, ...]   # S1 header cells
  source_cell_refs: tuple[PhysicalCellRef, ...]        # physical cells back it
  evidence_word_ids: tuple[str, ...]
```

```text
HeaderCellRef
  level: int
  column: int      # S1 header grid column
  grid_row: int    # physical header row
```

`HeaderCellRef` resolves to the existing S1 header id
`{table_id}-h{level:02d}-c{column:02d}`; it is not a `PhysicalCellRef`, because
one physical header cell can back several header ids.  `table_rebuilder`
resolves each ref into a domain `HeaderCell` with `source_header_cell_ids`,
`source_cell_ids` and `evidence_word_ids`.  Header
cell ids and column ids are not interchangeable: `column_id` is the logical
column, while the source lists identify the physical evidence.  The logical id
shape is `{table_id}-lh{level:02d}-c{logical_column:02d}`; S1 header ids are
untouched.  A logical header is never emitted with only its final text and no
physical source.

Three concepts stay separate:

* `logical_boundary_source` — why the boundary exists (`printed_rule`,
  `header_canopy`, `label_aligned`, `structural`, `subrule_promoted`);
* `logical_column_role` — the assigned role (`parameter`, `condition`,
  `unknown`, …);
* `role_source` — why that role was assigned (`header_text`,
  `subrule_short_label`, `fail_closed`, `section_band`).

A promoted boundary therefore does not by itself confirm a semantic role.

* a canopy cell backs every logical column it overlaps;
* sub-labels (`MIN`, `TYP`, `MAX`) are appended in header-level order;
* an empty printed header stays empty and its role is `unknown`;
* an unlabelled logical column that is not created by a promoted sub-rule is
  `unknown`.

`logical_column_roles` uses the existing `role_for_header` mapper.  Role
sources: `header_text`, `subrule_short_label`, `fail_closed`.  The physical
`headers` and `column_roles` fields stay as they are in S1; the logical fields
are additive and do not migrate S1 semantics (see §14 decision 9).

## 8. Fail-closed behaviour

The logical mapping is `unresolved` when any of the following holds:

* a partial separator has mixed short-label evidence below the promotion
  threshold;
* a candidate logical boundary has no evidence source at all;
* a section-like row has several populated label cells, so the single-label
  span rule cannot be applied (§7.3);
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

An unresolved logical mapping does **not** invalidate physical evidence.  Visual
fields, cell provenance, word ids and physical candidates remain valid and are
reported independently; `logical_mapping_unresolved` is a separate statistic,
not a physical failure.

## 9. Proposed data-model changes

All changes are additive with defaults.  No existing field is renamed,
removed or reinterpreted.  `extra="forbid"` models remain valid for old JSON.

### 9.1 New modules

`src/icpdf/domain/logical.py` (new; shared, serializable models so the domain
layer does not import the parser):

* `BoundaryEvidence`, `VisualBoundary`, `LogicalBoundary`, `ColumnMapping`
* `PhysicalCellRef`, `HeaderCellRef`, `LogicalHeaderRef`, `SectionBand`,
  `ConditionBand`, `ConditionContext`, `ContextRef`, `LogicalCell`
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
| `DetectedCell` | `logical_cell_ids: tuple[str, ...] = ()`, `logical_columns: tuple[int, ...] = ()`, `word_ids: tuple[str, ...] = ()` (derived caches; no single-valued logical id) |
| `DetectedRow` | `row_role: str = "data"`, `context_refs: tuple[ContextRef, ...] = ()` (it already has `grid_row`) |
| domain `Table` | the same logical/visual fields, as lists; `logical_header_cells: list[HeaderCell]` (logical `column_id`), resolved `physical_cell_ids` / `source_cell_ids`, and `condition_contexts` |
| domain `Cell` | `logical_cell_ids: list[str] = []`, `logical_columns: list[int] = []`, `word_ids: list[str] = []` |
| domain `HeaderCell` | additive `source_header_cell_ids: list[str] = []`, `source_cell_ids: list[str] = []`, `evidence_word_ids: list[str] = []`; existing `source_cell_id` is unchanged |
| domain `TableRow` | `grid_row: int \| None = None`, `row_role: str = "data"`, `context_refs: list[ContextRef] = []` |
| `Candidate` | physical identity is unchanged (`candidate_id` = document id + physical `cell_id`); additive `logical_cell_refs: list[str] = []`, `logical_columns: list[int] = []`, `context_path: list[ContextRef] = []`, `eligible_for_parameter_extraction: bool = True`, `eligible_for_context: bool = False`; `CandidateType` gains `SECTION = "section"` |
| `Candidate` roles | section rows use `candidate_type=SECTION`, `column_role=UNKNOWN`, `role_source="section_band"`, eligibility `false / true`; `unresolved_section_hint` rows keep physical candidate type but eligibility `false / true`; other candidates use the logical column role |
| `TableParams` | additive defaults only: `subrule_logical_span=0.85`, `section_bold_ratio=0.9`, `short_label_max_words=2`, `short_label_max_chars=12`, `short_label_band_ratio=0.5`, `visual_min_rule_span_pt=4.0`, `crossing_epsilon_pt=0.5`; the unit-only exclusion list is a separate auditable table in the same params module |

All thresholds live in `TableParams`; the algorithm functions contain no
scattered magic numbers.  The YAML config and its SHA
`ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c` stay
unchanged, but every run manifest records the effective parameter values
(including code defaults) and a parameter-snapshot hash, so a later change to a
code default cannot make an old run irreproducible.  The short-label unit-only
exclusion set is an explicit, auditable table in the params module rather than
opaque string matching.

### 9.3 Candidate and evidence traceability

A candidate is a **physical-cell object**, not a logical-cell object.  Its
identity is unchanged; the logical interpretation is attached as references.

`build_candidates` resolves the role through the candidate's logical refs:

* exactly one logical cell → use that logical column's role and header path;
* several logical cells with the same role → use that role;
* several logical cells with conflicting roles → `column_role = UNKNOWN`,
  `role_source = "multi_logical_mapping"`; both refs are kept and no role is
  forced;
* unresolved mapping → fall back to the S1 physical `headers` /
  `column_roles`, with no logical refs.

Candidate ids, cell ids, bboxes, raw text and unit extraction are unchanged.

* `candidate_id` remains `"{document_id}:{cell_id}"`; splitting one physical
  cell into several logical cells never creates new candidate ids.
* Every candidate gains `logical_cell_refs`, derived `logical_columns` and
  `context_path` when the mapping is decided, plus the eligibility flags.
* Every `LogicalCell` lists `physical_cell_refs` at parser level and
  `physical_cell_ids` in the domain table, plus `word_ids`; word ownership is a
  partition across logical cells (`word_ids` sets are disjoint).
* Every `LogicalHeaderRef` lists `source_header_cell_refs`, `source_cell_refs`
  and `evidence_word_ids`, resolved to the corresponding domain id lists.
* Every `VisualBoundary` / `LogicalBoundary` records its evidence source (rule
  component ids, header cell ids or label run) and coverage; an evidence-free
  logical boundary is an error.
* Section and condition bands record `source_cell_refs`, resolved to
  `source_cell_ids`; every `ConditionContext` lists its target candidates and
  association evidence.
* When the mapping is unresolved, candidate logical fields stay empty; no
  physical candidate is dropped or renumbered.

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

Synthetic P0-1 case — one physical cell split by a promoted boundary.  The
physical cell is unchanged; two logical cells reference it and their word sets
are disjoint:

```yaml
logical_cells:
  - logical_cell_id: syn-r05-lc01
    row_start: 5
    row_end: 5
    logical_column: 1
    logical_column_span: 1
    text: <words W1>
    physical_cell_refs: [{grid_row: 5, cell_index: 0, column_index: 1}]
    word_ids: [W1]
  - logical_cell_id: syn-r05-lc02
    row_start: 5
    row_end: 5
    logical_column: 2
    logical_column_span: 1
    text: <words W2 W3>
    physical_cell_refs: [{grid_row: 5, cell_index: 0, column_index: 1}]
    word_ids: [W2, W3]
```

The domain cell carries `logical_cell_ids: [syn-r05-lc01, syn-r05-lc02]`,
`logical_columns: [1, 2]`, `word_ids: [W1, W2, W3]`, while the candidate keeps
`candidate_id = "{document_id}:{cell_id}"` and lists both logical refs.

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

Every per-item report states `pred_logical_columns`, `gold_logical_columns` and
`logical_exact` explicitly, including known misses (CY29 P08: `9 / 12 /
false`), so a miss can never be hidden by denominator editing.  Each run
manifest records the effective `TableParams` values and their snapshot hash
(§9.2).

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
5. Row contract: `grid_row` values unique and non-negative; every
   `row_start` / `row_end` / `source_row` satisfies
   `0 <= row_start <= row_end <= n_rows - 1`; `row_role` in the fixed
   vocabulary; section bands do not overlap the header band and their
   `bold_ratio` is in `[0, 1]`.
6. Section/condition bands: source cell ids exist, visual/logical column
   indices valid; every context `band_id` resolves to a section or condition
   band, and a section ref's row is inside that band.
7. Logical cells: physical cell ids exist (domain) and every parser-level ref
   resolved to exactly one emitted cell; word ids resolve and are unique
   across the logical cells sharing a physical cell; logical column valid;
   section cells cover their band's logical columns; a logical cell with no
   `physical_cell_id` / `word_id` is an error.
8. Many-to-many consistency: for every physical cell, `logical_cell_ids` equals
   exactly the set of logical cells whose `physical_cell_ids` contain it;
   `logical_columns` equals the derived column set; a single-valued logical
   field on a physical cell is an error.
9. Headers: every logical header resolves to at least one
   `source_header_cell_ids` entry and one `source_cell_ids` entry;
   `evidence_word_ids`
   resolve; `logical_header_id` is unique; a logical header with text but no
   source evidence is an error.
10. Boundaries: every logical boundary has at least one allowed evidence
    source (§6 invariant 2); a promoted boundary records its short-label
    evidence.
11. Candidates: logical cell/column references resolve; section candidates
    have `candidate_type=SECTION`, a section `source_cell_id` and
    `eligible_for_parameter_extraction == false`; `unresolved_section_hint`
    rows have the same eligibility; unresolved tables carry no logical
    references; a `ConditionContext` target exists and its
    `association_evidence` is non-empty.

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
9. **P0-1 acceptance case**: one physical cell straddling a promoted boundary
   yields two logical cells that both reference the same physical cell; word
   sets are disjoint and the candidate keeps one physical `candidate_id`.
10. Section followed by data rows → row context closes at the next section.
11. A condition band associated by `header_path` / `column_map` attaches a
    context ref to the parameter candidate on the same row.
12. A logical header concatenated from two physical header cells keeps both
    `source_header_cell_ids`, both `source_cell_ids` and all
    `evidence_word_ids`.

Negative:

13. Bold numeric full-width row → not a section.
14. Bold multi-cell data row → not a section.
15. Header row with bold styling → not a section.
16. Merged solo non-bold row → `unresolved_section_hint`, no `SectionBand`, no
    SECTION candidate, candidate ineligible for parameter extraction.
17. Sub-rule with prose right side → demoted.
18. Sub-rule with numeric/unit right side → demoted.
19. Sub-rule with mixed label/prose evidence → `unresolved`.
20. `not_printed` table without stable labels → `unresolved`.
21. Whole-table bold with no solo rows → no section, mapping intact.
22. Condition band in an unrelated column on the same row → no
    `ConditionContext` (same-row membership is not evidence).
23. Word center exactly on a promoted boundary → `unresolved`, not an arbitrary
    assignment.
24. Logical header with text but no source refs → validator error.
25. Physical cell with a single-valued logical id, or a reverse map that does
    not match the logical cells → validator error.

### 12.2 Real PDF integration tests

`tests/integration/test_phase14_s2.py` (skips when PDFs are absent):

* MICRF103 P03: physical 30×6 unchanged; visual 6 / implied_outer; logical 6;
  section bands at zero-based grid rows 1/9/15/19 span 6.
* DS10 P04: section bands at zero-based grid rows 1/7/15/24 span 2; P05 rows
  1/12.
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
* Physical candidate ids and counts are identical before and after S2 on both
  frozen sets; every changed logical field is listed per item.
* Every row range in emitted structures satisfies the §7.0 contract.

## 13. Implementation slices after approval

| Slice | Content | Acceptance |
| --- | --- | --- |
| S2-design-r1 | this revision: many-to-many mapping, header provenance, row contract, `ConditionContext`, recorded decisions and red lines | Reviewer confirms this document; no code |
| S2a | new `logical_structure.py`; additive models; visual boundaries and status | visual 19/19 on the gold comparable set; physical diff empty |
| S2b | logical boundaries, demotion/promotion, many-to-many projection, header provenance, roles, fail-closed | logical 20/21; no physical change; unresolved tables keep physical payload; reverse-map consistency |
| S2c | section bands, SECTION candidates, `ConditionBand` + `ConditionContext`, `context_path` | MICRF section rows span 6, DS10 span 2; section candidates ineligible for extraction; candidate ids unchanged; no unconditional same-row context |
| S2d | evaluator visual/logical split, validator codes, frozen reruns and report | separate metrics with per-item `pred/gold/logical_exact`; validator 0/0; per-item physical diff empty; parameter snapshot recorded |

Each slice is a separate local commit with its full SHA in the report.  No push
to Codeup.  No slice is reported as accepted before Reviewer confirmation.

## 14. Reviewer decisions (r1)

The Reviewer answered all 12 questions from r0.  These decisions are binding
for S2 and are already folded into §§5–13:

| # | Topic | Decision | Binding constraint |
| --- | --- | --- | --- |
| 1 | Section evidence | Conditional approval | Bold ≥90% + solo populated cell is a high-confidence rule, not a definition.  Insufficient evidence → `unresolved_section_hint` diagnostic; never forced into a parameter candidate.  No background-fill/border detection in S2. |
| 2 | Old invariant | Approved | `logical_columns <= visual_columns` withdrawn.  Evidence-based invariants adopted; every logical boundary needs an allowed evidence source. |
| 3 | Section span | Approved with geometry | Crossing means clipped intersection length with the row band > `crossing_epsilon_pt` (0.5pt), never endpoint proximity.  Several populated label cells → unresolved. |
| 4 | Promoted role | Approved | `condition` / `subrule_short_label`; no adjacency inference.  `logical_boundary_source`, `logical_column_role` and `role_source` are separate fields. |
| 5 | Fail-closed | Approved | Whole-table `logical_columns = null`, `logical_mapping_status = "unresolved"`; physical payload and candidates retained; physical evidence validity is independent; `logical_mapping_unresolved` is a separate statistic. |
| 6 | Thresholds | Experimental approval | 0.85 coverage, 2 words, 12 chars, 0.5 band ratio, 0.90 bold, 4pt minimum span, 0.5pt crossing epsilon.  All live in `TableParams`; no magic numbers; runs record values and a parameter-snapshot hash; unit-only exclusion table is auditable. |
| 7 | CY29 P08 | Known miss accepted | Report `pred 9 / gold 12 / logical_exact false`; header-label splitting deferred to S4/a separate task; not excluded from the denominator. |
| 8 | Section rows | Approved | Rows stay in `rows` with `row_role = section` and context refs; `_ragged_rows` / `reconstruction_status` unchanged; section recognition never changes physical reconstruction state. |
| 9 | Physical vs logical fields | Approved, dual track | Keep `headers` / `column_roles`; add `logical_*`; no silent semantic migration of S1 fields. |
| 10 | `CandidateType.SECTION` | Conditional approval | Same physical `candidate_id`; SECTION is context evidence: `eligible_for_parameter_extraction = false`, `eligible_for_context = true`; P0-1 mapping fix comes first. |
| 11 | `TextSpan.flags` | Approved | Store raw `flags: int \| None`; `None` = unknown; bit 16 = bold; font-name parsing is fallback; missing flags are never treated as non-bold. |
| 12 | Condition shape | `ConditionBand` only | No `partial_condition_band` until Gold v2 contains a validated instance. |

No open question remains.  S2a begins only after the Reviewer confirms this
revision.

## 15. Non-goals

No S3 drawing/schematic gate; no S4 role expansion; no OCR/LLM/other engine;
no vendor/model/page special case; no Gold v2 edit; no detection or
`RuleComponent`/`TableRegion` change; no YAML config change; no Codeup push;
no acceptance version built from unreviewed metrics.  Additionally out of
scope: header-label column splitting (CY29 P08 stays a known miss),
background-fill / border-based section detection, a `partial_condition_band`
field, migration of S1 `headers` / `column_roles` semantics, and any
single-valued logical id on a physical cell.

## 16. Frozen acceptance red lines

These hold from S2a onward and may not be bypassed to improve a metric:

| Red line | Requirement |
| --- | --- |
| S1 physical structure | `grid.xs/ys`, cell bbox/text and region aggregation item-by-item unchanged |
| Candidate identity | Existing physical candidate ids and counts unchanged |
| Evidence | Every logical cell traces to physical cells and word ids |
| Header | Every logical header traces to source header cells |
| Fail-closed | Undecided mapping reports `unresolved`; no invented logical boundary |
| Section | SECTION never enters formal parameter output |
| Gold | Gold v2 unmodified |
| Evaluation | `unresolved` still counts in the logical denominator |
| Regression | Phase 1.2 46 items and Gold v2 21 items compared per item |
| Configuration | Thresholds recorded in the run parameter snapshot for reproducibility |
