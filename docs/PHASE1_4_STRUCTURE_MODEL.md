# Phase 1.4 structure model — design only

Status: design proposal.  **S1 (sections 2.1–2.2 and the region-aggregation
part of 2.3) is implemented** — see `docs/PHASE1_4_S1.md`.  **The S2 design and
data-model change proposal is `docs/PHASE1_4_S2.md`; it is submitted for
Reviewer confirmation and no S2 code has been written.**  S3/S4 remain design
only.  Parser parameters are frozen and Phase 2 stays frozen.  The purpose is
to agree on the object model and decision order before any change to
`icpdf.parser.table_detector`.

Inputs to this design:

* Gold v2 (`docs/GOLD_SPEC.md`, `gen-2026-11-06.2`, 21 tables / 8 negatives).
* The internal generalization run in `docs/PHASE1_3_GENERALIZATION.md`.
* The reviewer's structure priorities: outer borderless boundaries, merging
  components into one logical table, sub-rule versus logical column, drawing
  versus table, headerless lists (`header_rows = 0`), unlabeled columns stay
  `unknown`.

## 1. Why the current model fails

The detector currently treats one connected rule component as one table.  The
generalization set exposes four distinct failures of that equivalence:

| Observation | Failure family |
| --- | --- |
| MICRF103 p3: five components of one printed table; outer Symbol/Units columns have no vertical rule; parser emits 3 fragments and scores IoU 0.2335 | one table ≠ one component; outer boundary is implied |
| DS10CP152 p13: fully ruled table drawn as one `qu` outline per cell; parser emits nothing | ruling primitive coverage |
| CY29FCT520 p4/p5/p6, DS10CP152 p4/p5: body-only condition sub-rules; parser counts them as columns | visual boundary ≠ logical column |
| CY29 pinout, pipeline block diagram, package drawings, DS10 prose/schematic | drawing/schematic ≠ table |

The model below separates three objects that the current code conflates.

## 2. Object model

### 2.1 RulePrimitive

One physical ruling mark on a page, independent of whether it belongs to a
table:

```text
RulePrimitive
  kind:        line | thin_rect | quad_edge
  orientation: horizontal | vertical
  a, b:        extent along the axis
  c:           position on the perpendicular axis
  weight:      stroke width
  source:      drawing index + item index
```

`quad_edge` covers axis-aligned quadrilateral cell outlines.  A `qu` is not a
special table type; it is four ruling primitives.  This is the only addition
needed for DS10CP152-P13-T02.

### 2.2 RuleComponent

A connected component of primitives, unchanged in meaning:

```text
RuleComponent
  id, bbox
  horizontal: RulePrimitive[]
  vertical:   RulePrimitive[]
  page
```

A component is a **physical** object.  It carries no claim that it is a table,
and it is allowed to be a fragment, a figure frame or a drawing element.

### 2.3 TableRegion

An **aggregation** of one or more components that a reader would see as one
table area:

```text
TableRegion
  id, page, bbox
  components: RuleComponent[]
  outer_boundary: {left, right, top, bottom}
  boundary_source: ruled | implied_horizontal | implied_alignment | mixed
  row_bands: y intervals
  visual_separators: {x, coverage, span_ratio}[]
  merge_evidence: [...]
  confidence
```

`TableRegion` is the detection unit.  A region may be built from a single
component (most tables) or from several (MICRF103-P03).  It may also be built
from primitives that never formed a component because no vertical rule exists
in most of the table.

Rules:

1. **Components merge when their union stays a grid.**  Candidate merges are
   components whose bboxes overlap on the perpendicular axis and whose
   horizontal rule extents align within tolerance.  The merged region must
   have (a) consistent column positions from the union of verticals, (b) row
   bands that do not overlap illegally, and (c) a plausible cell density.
   MICRF103-P03 merges five sections because all five share the same column
   lattice and stack vertically with a section-title band between them.
2. **Outer boundaries may be implied.**  When no vertical rule exists at the
   left/right edge, the boundary is the common extent of the horizontal rules
   (or the aligned text block if horizontal rules are also absent).  This is a
   property of the region, not an invented component.
3. **Fragments do not suppress each other.**  If a component is a subset of a
   region's grid (same column lattice, contained row bands), it is absorbed,
   not emitted separately.  This is the MICRF 3-fragment case.

### 2.4 LogicalTable

A confirmed semantic table derived from a region:

```text
LogicalTable
  id, page, bbox
  region_ref
  header: HeaderModel
  visual_columns: int | null
  visual_status: printed | partial | implied_outer | not_printed
  logical_columns: LogicalColumn[]
  rows: RowBand[]
  cells: Cell[]
  roles: RoleAssignment[]
  negative_reason: null | drawing | schematic | pin_diagram | prose | layout
```

`LogicalTable` is the only object that may emit candidates and therefore the
only object compared with gold tables.

## 3. VisualBoundary versus LogicalColumn

### 3.1 VisualBoundary

A separator a reader can see: any vertical primitive with
`span_ratio = covered_height / region_height` above a small threshold.  This
includes body-only condition sub-rules and rules that stop at a group row.
The outer left/right edges count when ruled or when horizontal-rule extents
imply them.

`visual_columns` is the number of printed intervals, and `visual_status` is
`printed` / `partial` / `implied_outer` / `not_printed` exactly as Gold v2
defines it.

### 3.2 LogicalColumn

A semantic column used for headers and roles.  Its boundary evidence, in
descending strength:

1. a separator that spans the header band and the body and aligns with a
   header-cell boundary (`printed`);
2. a header canopy boundary derived from explicit merges
   (`header_canopy`);
3. a header label boundary inferred from label runs (`label_aligned`);
4. a full-height separator that survives the sub-rule test (`structural`).

### 3.3 Sub-rule test (priority 3 from the review)

A visual separator becomes a logical column boundary only if **both** hold:

* it aligns with a header boundary or a label boundary; or it spans at least
  `--subrule-logical-span` (default: 0.85) of the region height;
* splitting on it does not create a column whose cells are all empty or whose
  content is a continuation of the same attribute.

Otherwise it is a **condition attribute** of the covering logical column:
stored on the cell as `condition_path`, counted in `visual_columns`, and
excluded from `logical_columns`.  This directly encodes the observed
CY29FCT520-P04/P05/P06 and DS10CP152-P04/P05 sub-rule bands.

Invariants (corrected in the S2 proposal; the earlier
`logical_columns <= visual_columns` ordering is withdrawn because Gold v2 has
8 logical / 4 visual on CY29FCT520-P04-T01 and 9 logical / 7 visual on P05):

* `not_printed` tables have `visual_columns = null` and a decided logical
  mapping from header/label evidence only;
* otherwise every logical boundary is a visual boundary or carries
  header/label evidence, and every visual column overlaps at least one logical
  column while every logical column overlaps at least one visual column;
* a visual column may overlap several logical columns (header canopy), and
  several visual columns may map to one logical column (demoted sub-rule).

See `docs/PHASE1_4_S2.md` §6 for the full set.

## 4. Decision order

The order matters; later stages may not override earlier rejections without
new evidence.

1. **Primitives** — collect lines, thin rects and quad edges; merge collinear
   spans.
2. **Components** — connected components as today (now including quad edges).
3. **Regions** — merge components, derive implied outer boundaries.  A region
   is a detection candidate.
4. **Table-versus-drawing gate** — before structure inference:
   * require either a column lattice that repeats across at least two row bands
     or a header band with at least two labels;
   * reject when the region is dominated by drawing primitives (long curved
     paths, arrows, dimension ticks) without repeated cell content;
   * reject when text is only labels attached to figure geometry (pin names
     around a package, boxed stage labels in a block diagram);
   * reject prose bands (no repeated value columns, no header alignment).
   A rejected region records `negative_reason` for audit.
5. **Header model** — detect depth from canopy merges; if no header band is
   found, emit `header_rows = 0` rather than inventing a header from a bold
   first row.
6. **Visual columns** — all qualifying vertical primitives, including partial
   ones; compute `span_ratio` per separator.
7. **Logical columns** — apply §3.3; demote sub-rules to condition attributes.
8. **Cells and rows** — assign words to the visual grid, then project onto
   logical columns; keep `condition_path` for demoted boundaries.
9. **Roles** — assign only in this order: header-cell text (`header_text`),
   explicit label evidence (`label`), weak content heuristic (`heuristic`),
   otherwise `unknown`.  An unlabeled column never defaults to `symbol`.
10. **Evidence assembly** — every accepted table carries region,
    visual/logical separators, header cells, role source and rejection reason
    when applicable.

## 5. Specific decisions requested by the review

| Priority | Decision in this model |
| --- | --- |
| Outer borderless boundaries | Region-level `implied_horizontal`: common horizontal-rule extent. Do not require a vertical component. MICRF103-P03 becomes one region. |
| Merge components into one logical table | Stage 3 merge test: shared column lattice + non-overlapping stacked row bands + plausible cell density. Fragments inside a region are absorbed (no duplicate emission). |
| Sub-rule vs logical column | §3.3 two-part test; demoted separators become `condition_path` attributes, not columns. |
| Drawing/schematic vs table | Stage 4 gate with explicit rejection reasons; drawings still count as negative samples, but no table candidates are emitted. |
| Headerless lists | `header_rows = 0` when no header band passes the canopy/label test; never infer a header from bold styling alone. |
| Unlabeled columns stay `unknown` | Role order ends at `unknown`; no leading-column symbol guess. |

## 6. How this addresses the measured failures

| Case | Current result | Expected under this model |
| --- | --- | --- |
| MICRF103-P03-T01 | FN, 3 fragments, best IoU 0.2335 | one region from 5 components with implied outer boundary → one table |
| DS10CP152-P13-T02 | FN, IoU 0.0 | quad edges become primitives → full 2-column grid |
| CY29FCT520-P05 | 11 predicted columns | sub-rules demoted; 9 logical columns, 7 visual |
| CY29FCT520-P06 | 6 predicted columns | unlabeled band stays a column but role unknown; 7 logical |
| CY29FCT520-P08 | 9 predicted columns | label-aligned logical columns, `not_printed` visual status |
| DS10CP152-P04/P05 | 7 predicted, 8 visual gold | visual count reported separately; logical stays 7 |
| pinout / block diagram / package drawing / schematic / prose | 4 negative FPs | stage-4 rejection reasons; no candidate |
| DS10CP152-P03-T01 | invented header | `header_rows = 0` |

These are hypotheses to test in Phase 2 of the structure work, not claims of
already-achieved results.

## 7. Metrics alignment

The design deliberately mirrors Gold v2 so the evaluator needs no new
concepts:

* `visual_columns` / `visual_status` / `partial_boundaries` → visual boundary
  exactness;
* `logical_columns` → logical column exactness, header attribution and role
  accuracy;
* `negative_reason` → negative FP attribution by kind;
* `condition_path` is evidence only and is not scored as a column.

Until the parser emits both representations, evaluation keeps comparing its
single column count against the respective gold count, as documented in
`docs/GOLD_SPEC.md`.  The S2 proposal (`docs/PHASE1_4_S2.md` §10) replaces
this with independent `pred_visual_columns` and `pred_logical_columns` while
keeping the legacy physical count as a separate regression line.

## 8. Invariants and validation

1. No table without a region; no candidate without a logical table.
2. The evidence-based visual/logical invariants in §3.3 (the old
   `logical_columns <= visual_columns` ordering is withdrawn).
3. Every sub-rule demotion is recorded with its `span_ratio` and the covering
   logical column.
4. Every role has a source; `unknown` is a valid terminal source.
5. Every rejected region has a `negative_reason` from the fixed vocabulary.
6. `tools/validate_evidence --strict` must pass before any metric is reported.

## 9. Non-goals and constraints

* No LLM, no learned classifier, no per-vendor or per-document special case.
* No change to parser parameters until this design is reviewed; the frozen
  generalization runs stay the baseline.
* No gold tuning to make a metric pass.
* Cross-page continuation is out of scope for this phase but must not be
  blocked by the object model (a LogicalTable may later have page fragments).

## 10. Proposed implementation slices (after approval)

| Slice | Content | Acceptance |
| --- | --- | --- |
| S1 | RulePrimitive (including quad edges) + region aggregation with implied outer boundary | MICRF103-P03 one table; DS10CP152-P13-T02 detected; Phase 1.2 detection unchanged |
| S2 | Visual vs logical separators + sub-rule demotion + condition_path | CY29/P05, P06 and DS10/P04, P05 column counts align with gold; visual metric reported |
| S3 | Drawing/schematic/prose gate with rejection reasons | 4 remaining negative FPs removed without losing accepted tables |
| S4 | Headerless/unknown role rules | DS10 P03-T01 header_rows=0; `unknown` recall > 0; Phase 1.2 roles unchanged |

Each slice is evaluated on the frozen runs and the Phase 1.2 regression set;
no slice is accepted if it trades a Phase 1.2 regression for a generalization
gain.
