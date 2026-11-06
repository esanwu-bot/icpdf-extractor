# Phase 1.4 S2b — Logical Boundary Lattice and Projection

**Status:** design proposal only. No implementation, schema change, Gold change
or pipeline integration is authorized by this document. Implementation starts
only after Reviewer approval.

**Relationship to the approved S2 design:** `docs/PHASE1_4_S2.md` remains the
umbrella design. S2b narrows its §5–§7 to the logical column lattice and the
physical→logical projection. Where this document is more specific, it is a
proposal for review, not a replacement of the approved principles.

## 1. Problem

S2a established that the visual boundary evidence is trustworthy: every
persisted segment resolves to real PDF primitives. S2b addresses a different
question:

> Which printed and structural facts justify treating a boundary as a logical
> column boundary, and how are physical cells projected onto those logical
> columns without changing the physical grid?

The two lattices are not interchangeable. Gold v2 contains tables where logical
columns exceed visual columns (header canopies) and tables where visual columns
exceed logical columns (body condition sub-rules). The current logical count is
18/21; S2b must make the reasoning explicit and auditable rather than infer a
count from cell content.

Success means:

- every kept logical boundary has at least one allowed evidence source;
- every logical column carries a traceable physical-column projection;
- every logical cell carries physical cell references and a disjoint word set;
- undecidable cases fail closed at table level instead of guessing;
- S1 physical fields and S2a visual fields are byte-for-byte unchanged.

## 2. Hard constraints

S2b must not:

- change `grid.xs`, `grid.ys`, physical cell bboxes/text, `column_index`,
  `row_span`, `column_span`, cell ids, Candidate ids or candidate identity;
- re-interpret or overwrite S2a `visual_*` fields;
- add a boundary because a target column count, a Gold value or a desired
  extraction result suggests one;
- use an LLM to propose, rank or select logical boundaries;
- change Gold v1/v2 or tune existing visual thresholds;
- implement S2c (`ConditionContext` / `ConditionBand`), section-band semantics or
  Product Identity Resolution;
- push to Codeup.

S2b is an additive, derived annotation. The physical table remains the only
source of cells, text and candidates.

## 3. Design principles

1. **Derived, not re-gridded.** Logical columns are intervals over the frozen
   physical grid; they never delete or renumber physical columns.
2. **Evidence first.** A boundary is kept only for an allowed evidence source.
   Absence of evidence is not evidence for a split.
3. **Deterministic.** All candidate ordering, grouping and tie-breaks are total
   and independent of input order.
4. **Fail closed.** Ambiguity is represented explicitly and suppresses the
   table's logical payload; it is never resolved by a default guess.
5. **Additive compatibility.** New fields have defaults; old runs still load and
   still report no logical mapping.

## 4. Data model (deliverable 1)

All models below are frozen Pydantic models. Parser-level models live beside
`DetectedTable`; domain models mirror the same fields in `domain/table.py`.

### 4.1 Enums

```text
LogicalMappingStatus = "resolved" | "unresolved"
LogicalBoundaryRole   = "outer_left" | "outer_right" | "internal"
LogicalBoundarySource = "printed_rule" | "header_canopy" | "label_aligned"
                      | "structural" | "subrule_promoted"
LogicalBoundaryDecisionKind = "keep" | "demote" | "unresolved"
```

`logical_mapping_status` is table-level. A legacy table or a table with no
decidable logical lattice is `unresolved`, not a third silent state.

### 4.2 `LogicalBoundary` (kept boundary)

```text
LogicalBoundary
  x: float
  role: LogicalBoundaryRole
  sources: tuple[LogicalBoundarySource, ...]   # non-empty, sorted
  visual_boundary_x: float | None              # nearest S2a boundary, if any
  visual_coverage: float | None                # copied from S2a, not recomputed here
  evidence: tuple[LogicalBoundaryEvidence, ...]  # non-empty
```

Only kept boundaries appear in `DetectedTable.logical_boundaries`. Demoted and
unresolved candidates are recorded separately (§4.3) so the decision remains
auditable without polluting the accepted lattice.

### 4.3 `LogicalBoundaryDecision` (diagnostic, every candidate)

```text
BoundarySupport
  band_count: int
  rule_bands: int              # bands with a printed rule at x
  gutter_bands: int            # bands with a body gutter at x
  crossing_bands: int          # bands where a word run crosses x
  short_label_bands: int       # bands with a right-side short label
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
  demoted_to: "condition_path" | None          # only when decision == "demote"
  support: BoundarySupport
```

This is a diagnostic record. It is retained even when the table is `unresolved`,
but it is never consumed by extraction and never treated as a logical lattice.

### 4.4 Evidence records

```text
LogicalBoundaryEvidence
  kind: "printed_rule" | "header_canopy" | "label_aligned" | "structural"
  # printed_rule: reference the S2a record rather than duplicating primitives
  visual_boundary_x: float | None
  visual_segment_refs: tuple[tuple[int, int], ...]  # (boundary index, segment index)
  # header_canopy: the printed header cells whose edge or gap is at x
  header_cell_refs: tuple[HeaderCellRef, ...]
  # label_aligned: body gutters and their row bands
  grid_rows: tuple[int, ...]
  word_ids: tuple[str, ...]
  # structural: repeated physical cell edges that make the boundary real
  physical_rule_component_ids: tuple[int, ...]
  physical_cell_refs: tuple[PhysicalCellRef, ...]
```

`HeaderCellRef` is the existing `(level, column, source_row, source_column,
bbox, text)` tuple, reused by reference; S2b does not create a second header
extraction.

### 4.5 Projection models

```text
PhysicalColumnOverlap
  region_component_id: int | None       # RuleComponent/region source, if known
  grid_row_start: int                   # inclusive
  grid_row_end: int                     # inclusive
  physical_column: int                  # 0-based interval in frozen grid.xs
  overlap_left: float
  overlap_right: float
  overlap_fraction: float               # overlap width / physical column width

ColumnProjection
  logical_column: int
  left: float
  right: float
  physical_columns: tuple[PhysicalColumnOverlap, ...]  # non-empty
  visual_columns: tuple[int, ...]                      # S2a intervals overlapped

LogicalColumn
  logical_column: int
  projection: ColumnProjection
  header_path: tuple[str, ...]          # top-to-bottom, may be empty
  header_cell_refs: tuple[HeaderCellRef, ...]
  role: ColumnRole                      # existing vocabulary; "unknown" allowed
  role_source: "header" | "subrule_short_label" | "unknown"
```

`PhysicalColumnOverlap.grid_row_start/end` is what makes a logical column able
to project onto several physical regions when stacked components share one
table: the same logical column may have one overlap per region/row band, and the
physical column indices may differ between bands. `region_component_id` links
the overlap back to `region_components`.

### 4.6 Logical cells

```text
PhysicalCellRef
  grid_row: int          # GridCell.row
  cell_index: int        # index inside DetectedRow.cells
  column_index: int      # DetectedCell.column_index, for readability

LogicalCell
  logical_cell_id: str                 # deterministic, content-independent
  row_start: int                       # inclusive physical grid row
  row_end: int                         # inclusive
  logical_column: int
  logical_column_span: int             # >= 1
  bbox
  text
  kind: "header" | "data"              # section/condition deferred to S2c
  physical_cell_refs: tuple[PhysicalCellRef, ...]
  word_ids: tuple[str, ...]            # disjoint across logical cells
```

The physical→logical cell relation is many-to-many and lives on the logical
side. A reverse cache `logical_cell_ids` on `DetectedCell` is derived, never
authoritative.

### 4.7 Additive table fields

`DetectedTable` / domain `Table` gain:

```text
logical_mapping_status: LogicalMappingStatus = "unresolved"
logical_mapping_reason: tuple[str, ...] = ()
logical_boundaries: tuple[LogicalBoundary, ...] = ()
logical_columns: int | None = None
column_projection: tuple[ColumnProjection, ...] = ()
logical_columns_detail: tuple[LogicalColumn, ...] = ()
logical_cells: tuple[LogicalCell, ...] = ()
logical_boundary_decisions: tuple[LogicalBoundaryDecision, ...] = ()  # diagnostic
```

`logical_boundary_decisions` is the only diagnostic payload retained on an
`unresolved` table; all accepted logical payloads stay empty (§9).

`DetectedCell` / domain `Cell` gain only derived caches:

```text
logical_cell_ids: tuple[str, ...] = ()
logical_columns: tuple[int, ...] = ()
word_ids: tuple[str, ...] = ()
```

Candidate identity is unchanged. Candidates may gain `logical_cell_refs` and
derived `logical_columns`; when the mapping is unresolved these are empty.

### 4.8 New parameters

All new thresholds are `TableParams` fields, included in
`table_params_snapshot()` and therefore in `table_params_sha256`. They are not
hidden constants. Proposed defaults, subject to Reviewer approval:

| Parameter | Proposed default | Purpose |
| --- | --- | --- |
| `logical_label_min_band_ratio` | 0.60 | stable body-gutter support |
| `logical_label_min_bands` | 2 | minimum supporting row bands |
| `logical_subrule_promote_min_ratio` | 0.50 | short-label promotion |
| `logical_subrule_promote_min_bands` | 2 | minimum supporting bands |
| `logical_subrule_ambiguous_min_ratio` | 0.25 | lower bound of the ambiguous band |

Boundary alignment uses the existing `visual_boundary_tol_pt` (2.5pt); no new
geometry tolerance is introduced. Adding fields requires
`TABLE_PARAMS_SNAPSHOT_VERSION = "table-params/v2"` for new runs; old snapshots
remain readable and keep their recorded v1 hash.

## 5. Candidate generation and decisions (deliverable 4)

### 5.1 Candidate set

Candidates are the union of:

1. internal positions of the frozen `grid.xs` (the recognition lattice);
2. S2a visual boundaries inside the table bbox;
3. header-canopy edges: left/right edges of `DetectedHeaderCell` bboxes that
   fall inside the table;
4. stable body gutters at x where no word crosses and at least
   `logical_label_min_bands` row bands have a gutter.

Candidates within `visual_boundary_tol_pt` are grouped into one candidate; the
group x is the mean, and every source remains listed. Candidates outside the
table bbox or within tolerance of an outer edge are not internal boundaries.

The two table bbox edges are always kept as `outer_left` / `outer_right` with
source `structural`. When an outer edge is not printed, the region's horizontal
extent is the evidence; no vertical rule is fabricated.

No candidate is generated from a target count, a Gold value, a header label
alone or a cell's semantic content.

### 5.2 Decision table

For each grouped candidate, in deterministic x order:

| Evidence at x | Decision | Source |
| --- | --- | --- |
| S2a full-height printed rule (`coverage >= 0.85`) | keep | `printed_rule` |
| partial rule, short labels on the right in >= 50% of non-empty bands and >= 2 bands | keep | `subrule_promoted` |
| partial rule, short-label ratio in `[0.25, 0.50)` and >= 2 bands | **unresolved** | — |
| partial rule, otherwise | demote to `condition_path` | — |
| no rule, aligned with a distinct header-cell gap/edge at >= 1 header level | keep | `header_canopy` |
| no rule, stable body gutter meeting the label thresholds and no crossing text | keep | `label_aligned` |
| no rule/header, candidate aligned with a repeated physical cell edge in >= 2 row bands and no word crosses | keep | `structural` |
| none of the above: no allowed evidence at x | demote (record `boundary_no_evidence`) | — |
| a body data cell crosses x in every band where the candidate otherwise has support | **unresolved** | — |
| sources disagree on keep/demote after grouping | **unresolved** | — |

A `colspan` body data cell is never evidence for a split. A crossing in a
header/section row does not veto a boundary supported in body rows. A full-height
printed rule inside a body merged cell is conflicting physical evidence, not
proof of a split.

### 5.3 Sub-rule promotion

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
  bands → promote, 6 → 7 logical columns.
- CY29FCT520 P05 `193.9`, `266.0`, right side is condition prose → demote.
- DS10CP152 P04 `346.1`, P05 `363.1`, right side is numeric/unit content →
  demote.

No threshold may be adjusted after seeing S2b results; changes require a new
design review.

### 5.4 Header-canopy boundaries

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
against 4 visual columns.

### 5.5 Demotion

A demoted boundary is not a logical column boundary. It is recorded in
`logical_boundary_decisions` with `demoted_to = "condition_path"` and is
available to S2c as a condition attribute; S2b does not emit condition bands.
The physical grid still contains that x; only the logical lattice ignores it.

## 6. Physical→logical mapping (deliverable 2)

### 6.1 Interval mapping

`ColumnProjection` is overlap-based, not a partition:

- one logical column may contain several physical columns (demoted sub-rules,
  wide condition columns);
- one physical column may be split into several logical columns (promoted
  sub-rules, header canopies);
- a logical column may project onto different physical columns in different
  row bands when stacked regions share one table.

For each logical column `[left, right]`, compute the overlap with every physical
column interval `[grid.xs[i], grid.xs[i+1]]` that intersects it. Record only
positive overlaps. `overlap_fraction` is the overlap width divided by the
physical column width; it is informational and does not filter the mapping.

### 6.2 Multi-region mapping

When the table aggregates several `region_components` (stacked row bands), the
same logical column may have one `PhysicalColumnOverlap` per contributing
region. The overlap records the region component and the inclusive grid-row
range it covers. This is the many-to-one mapping the Reviewer required: one
logical column, several physical regions.

If two regions use different physical x lattices, the logical column remains one
semantic interval; each region's overlap is recorded separately. No region is
allowed to renumber the global grid.

### 6.3 Cell projection

For each physical row and logical column:

1. find physical cells whose bbox intersects the logical interval;
2. assign each `TextWord` by its center x to exactly one logical column; a word
   center exactly on a boundary goes left, deterministically, and the tie is
   recorded in the decision diagnostics;
3. if several physical cells fall in one logical column, emit one `LogicalCell`
   whose `physical_cell_refs` lists all of them and whose text is their
   reading-order concatenation;
4. if a physical cell straddles a logical boundary, its words are partitioned;
   the cell appears in several `LogicalCell.physical_cell_refs`, but no word is
   duplicated;
5. `word_ids` across all logical cells form a disjoint partition of the words
   assigned to the table.

A physical cell may be referenced by several logical cells (header canopy,
section-like spanning cell, or word-level split). The reverse cache on the
physical cell lists all of them.

### 6.4 Mapping examples

- CY29FCT520 P04: visual column 1 contains logical MIN/NOM/MAX; one physical
  column maps to three logical columns.
- CY29FCT520 P05: visual columns 1–3 form one condition logical column; three
  physical columns map to one logical column.
- MICRF103 P03: six visual columns and six logical columns; the outer edges are
  implied, not printed, and the mapping must not invent a seventh column.

## 7. Merged cells and multi-level headers (deliverable 3)

### 7.1 `colspan`

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

### 7.2 Multi-level headers

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

### 7.3 Blank and headerless areas

- A fully ruled, entirely blank physical column stays in the logical lattice
  with `role = "unknown"`; its boundaries are kept as `printed_rule` because the
  full-height printed rules are the evidence.
- A wide blank gutter with no rule, no header and no stable body gutter is not
  a candidate and cannot create a logical column. If such an x came from a
  speculative `grid.xs` soft split, it is demoted (`boundary_no_evidence`); a
  full-height printed rule is handled by the first bullet, not by this one.
- A table with no header at all may still have a decided logical lattice from
  printed rules and body gutters; header paths are empty and are not a failure.

## 8. Evidence chain (deliverable 5)

Every accepted logical fact must be walkable back to the source:

```text
LogicalBoundary
  -> LogicalBoundaryEvidence
     -> S2a VisualBoundary / VisualSegment / primitive_indices
     -> DetectedHeaderCell (level, source_row, source_column, bbox)
     -> body word_ids and grid rows
LogicalColumn
  -> ColumnProjection -> PhysicalColumnOverlap -> grid.xs interval + region
  -> HeaderCellRef -> DetectedHeaderCell
LogicalCell
  -> PhysicalCellRef (grid_row, cell_index, column_index)
  -> word_ids -> TextWord.word_id (deterministic page-level id)
```

No logical record may carry an x, label or text that is not backed by one of
these references. The audit path is read-only and separate from the formal
validator; it re-resolves references against a fresh parse and refuses missing
or contradictory evidence.

`LogicalBoundaryEvidence.visual_segment_refs` uses the S2a record by index
rather than copying primitive indices, so there is one primitive provenance
chain, not two.

## 9. Failure strategy (deliverable 6)

### 9.1 Table-level fail-closed

If any candidate is `unresolved`, or any mapping invariant fails:

```text
logical_mapping_status = "unresolved"
logical_mapping_reason = (stable reason codes)
logical_columns = None
logical_boundaries = ()
column_projection = ()
logical_columns_detail = ()
logical_cells = ()
```

`logical_boundary_decisions` remains available for diagnosis, but it is marked
non-authoritative and is not consumed by extraction. The physical table, S2a
visual fields and candidates remain exactly as before.

### 9.2 Reason codes

Proposed stable codes:

```text
boundary_ambiguous_subrule_ratio
boundary_conflicting_sources
boundary_data_cell_crossing
boundary_header_gap_too_wide
boundary_no_evidence
mapping_physical_overlap_missing
mapping_word_not_assigned
header_level_tie
header_missing_for_canopy
region_lattice_inconsistent
```

A table may carry several codes. Codes are evidence for review, not an
alternative decision mechanism.

### 9.3 No guessing

- Never choose the interpretation that yields a target column count.
- Never choose the interpretation that improves a metric or matches Gold.
- Never fill a missing header from a neighbour.
- Never create a logical column from an empty interval.
- Never downgrade an ambiguity to a demotion to keep the table `resolved`.

## 10. Invariants and validator checks

Proposed invariants, checked by a new read-only validator (not the S2a
validator):

1. `logical_columns is null` iff `logical_mapping_status == "unresolved"`;
   unresolved tables carry no accepted logical payload.
2. `logical_boundaries` are sorted, unique, inside the table bbox and every
   internal boundary has at least one allowed source.
3. `logical_columns == len(logical_boundaries) - 1` when resolved.
4. Every logical column has a non-empty `ColumnProjection`; every physical
   overlap lies inside `grid.xs`; every logical column overlaps at least one
   physical column and vice versa.
5. Every kept boundary is within `visual_boundary_tol_pt` of an S2a visual
   boundary or has header/label/structural evidence.
6. `logical_cells` words are a disjoint partition; every referenced physical
   cell exists; every word id exists on the page.
7. Header references exist, belong to the table, and their levels are within
   `header_rows`.
8. Physical and S2a fields are unchanged: `grid.xs`, `grid.ys`, cell bboxes,
   cell text, `column_index`, `row_span`, `column_span`, `visual_boundaries`,
   `visual_boundary_status`, `visual_columns`, `partial_boundaries`,
   `visual_boundary_evidence`.
9. Candidate ids and counts are unchanged; candidate logical refs are empty on
   unresolved tables.
10. Old run artifacts without logical fields still load and are treated as
    `unresolved`, not as a parse failure.

## 11. Evaluation set and metrics

### 11.1 Three-layer evaluation set

**A. Regression set (must not change).**

- Phase 1.2: 46 tables + 19 negatives.
- Phase 1.3 and 1.4 samples, including the six S2a PDFs.
- Gold v2: 67 items, 21 with a decided logical mapping.
- Checks: S1 physical fields and S2a visual fields zero-diff; candidate ids and
  counts zero-diff.

**B. Logical-structure set (new, separately frozen).**

Cases required, each with its own annotation and source PDF SHA:

- cross-column canopy header;
- multi-level header with merged levels;
- merged data cell (`colspan` / `rowspan`);
- blank separator column;
- several physical columns forming one logical field;
- one physical cell referenced by several logical semantics;
- stacked regions sharing one logical column.

Known v2 examples can seed this set (CY29FCT520 P04/P05/P06/P08, MICRF103 P03,
DS10CP152 P04/P05/P11), but the set is stored under a new `gold/s2b/` (or
equivalent) version with its own manifest and SHA. Gold v2 is never edited.

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

### 11.2 Metrics

| Metric | Definition | Denominator |
| --- | --- | --- |
| LogicalBoundary precision / recall | matched kept boundaries within 2.5pt vs gold boundaries | predicted / gold boundaries |
| LogicalColumn exact match | predicted count and ordered intervals equal gold | tables with a decided gold mapping |
| Physical→logical mapping exact match | each logical column's physical column set and row-band overlaps equal gold | tables with a decided gold mapping |
| LogicalCell projection exact match | row range, logical column span, physical cell set and word partition equal gold | annotated projection cases |
| Header provenance coverage | logical columns with a complete, existing header cell chain | labelled logical columns |
| Ambiguous detection recall | gold-ambiguous cases predicted unresolved | gold-ambiguous cases |
| Zero-regression | S1/S2a/candidate fields byte-identical | all regression tables |

Report per-item results and a failure list; never report only a single exact
match. A boundary count match with a wrong physical mapping is a failure, not a
pass.

### 11.3 Anti-overfitting rules

- Freeze the S2b evaluation manifest and SHAs before the first prototype run.
- Fix the proposed parameters before seeing results; any change requires a new
  design review and a new evaluation version.
- Do not add a table to the set because it fixes a metric; do not remove a
  failing table.
- Do not use Gold logical counts as an input to the algorithm, directly or
  indirectly.

## 12. Staged delivery and review gates

| Stage | Deliverable | Allowed changes | Gate |
| --- | --- | --- | --- |
| S2b-Design | this document | docs only | Reviewer approval required |
| S2b-Schema | models, additive fields, read-only validator, unit tests | no detector integration; no S1/S2a/Gold change | Reviewer checks schema and invariants |
| S2b-Prototype | logical lattice on the standalone S2b set | no pipeline integration; no extraction dependencies | Reviewer checks boundaries, mapping, failure behavior |
| S2b-Integration | detector/rebuilder integration, full regression, compatibility report | additive wiring only; no physical or S2a change | Reviewer checks zero regression and evidence completeness |

No stage may begin before the previous gate is approved. S2b-Integration is not
authorized by S2a freeze or by this design.

## 13. Open decisions for Reviewer

1. Approve the proposed logical parameters and the `table-params/v2` snapshot
   version, or request different defaults before implementation.
2. Approve retaining `logical_boundary_decisions` as a non-authoritative
   diagnostic on unresolved tables (accepted payload remains empty).
3. Confirm that a fully ruled blank column is kept as a `printed_rule` logical
   column with `role = "unknown"`, rather than treated as an unresolved case.
4. Confirm that section-band semantics and condition bands remain out of S2b
   and are deferred to S2c.
5. Confirm that header-canopy boundaries may be added where `grid.xs` has no
   boundary, as long as the physical grid is untouched.
6. Confirm the location/name of the new S2b evaluation set and its freeze
   procedure.

## 14. Acceptance checklist for the design gate

- [ ] Six deliverables are answered: data model, mapping, merged cells,
      boundary decisions, evidence chain, failure strategy.
- [ ] Hard constraints in §2 are accepted.
- [ ] Proposed parameters and snapshot version are approved or amended.
- [ ] S2b evaluation set, metrics and anti-overfitting rules are approved.
- [ ] No implementation is authorized until this design gate passes.
