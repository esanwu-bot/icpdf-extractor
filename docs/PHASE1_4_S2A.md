# Phase 1.4 S2a — VisualBoundary (visual boundary lattice)

Status: S2a implementation + Reviewer-round r1 clarification + r2 primitive
audit, local commits only, **awaiting Reviewer**.  S2b (logical boundary /
logical projection) and S2c (`ConditionContext`) are not started.  No
acceptance is self-declared.

Round r2 adds an independent integration audit that re-opens the source PDFs,
re-runs `collect_primitives()`, rebuilds the `RuleComponent` set, and resolves
every recorded `primitive_indices` entry to the real `RulePrimitive`; it does
not touch the validator, the visual algorithm or any threshold.  The audit
refuses to run unless the PDF SHA-256 and the parameter snapshot match the
run manifest, and it reads its thresholds from that snapshot.  See §5.2 and
§7.4.

This revision answers the three S2a review items without widening scope:

* **P1 status precedence** — `partial` is now driven *only* by internal
  separators; a short or missing outer edge can never make a table `partial`.
  The rule is stated as a table in §3.1 and covered by four asymmetric/combined
  synthetic tests.
* **P2 evidence provenance** — every boundary carries `segments`
  (`component_id`, clipped `y0`/`y1`, page-level `primitive_indices`).  The
  validator recomputes coverage from those spans instead of trusting the
  stored `coverage`; implied outers carry no fabricated segment.  A real
  DS10CP152 sample is in §3.3.
* **P3 determinism** — segments are sorted by `(x, y0, y1, component_id)` and
  grouped against a fixed anchor, not a running mean, so input order and
  chain drift cannot change the lattice (§3.2).

The first-pass S2a runs had no segment evidence and are superseded by the
`runs/phase14_s2a/review_r1/` runs in §7.  No threshold, Gold file or S1
physical rule was changed.

Scope actually delivered, per the S2a authorization:

* visual boundary derivation from printed vertical ruling, attached to
  `DetectedTable` and the domain `Table`, with segment-level provenance back
  to `RuleComponent` / `RulePrimitive`;
* visual fields in the gold evaluator (separate denominator, legacy fallback
  for Gold v1);
* visual invariants in `tools/validate_evidence.py`, including independent
  coverage recomputation from recorded segments;
* new `TableParams` fields plus a canonical parameter snapshot and SHA-256 in
  every run manifest;
* unit/integration tests and a six-PDF rerun against the frozen gold sets.

Not delivered (still frozen): `grid.xs` / `grid.ys`, physical cell bbox/text,
Candidate IDs, logical boundaries, logical projection, `ConditionContext`,
Gold v2 (`gen-2026-11-06.2`), Phase 1.2 gold, the Candidate Registry and the
Evidence Validator's existing checks.

The parser YAML config is untouched; every run below reports the frozen config
SHA `ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c`.

## 1. Changed files

| File | Change |
| --- | --- |
| `src/icpdf/domain/visual.py` | **new**; frozen `VisualBoundary` (`x`, `role`, `drawn`, `coverage`, `component_ids`, `segment_count`, `segments`), frozen `VisualSegment` (`component_id`, `y0`, `y1`, `primitive_indices`) and the role/status vocabularies |
| `src/icpdf/parser/visual_structure.py` | **new**; `VisualStructure` and `build_visual_structure(region, params)` |
| `src/icpdf/parser/config.py` | `visual_min_rule_span_pt=4.0`, `visual_boundary_tol_pt=2.5`, `visual_full_height_coverage=0.85`; `table_params_snapshot`, `snapshot_sha256`, `table_params_sha256` |
| `src/icpdf/parser/table_detector.py` | `DetectedTable` additive fields `visual_boundaries`, `visual_boundary_status`, `visual_columns`, `partial_boundaries`, `visual_boundary_evidence`; builds them per accepted region |
| `src/icpdf/domain/table.py` | matching additive fields on `Table` + invariants |
| `src/icpdf/parser/table_rebuilder.py` | copies the five visual fields into `Table` |
| `src/icpdf/parser/pipeline.py` | writes `table_params` and `table_params_sha256` into both `run_config.json` and `run_manifest.json` |
| `tools/goldset/evaluate.py` | visual prediction/status metrics, separate denominator, legacy fallback, CSV columns, Markdown rows |
| `tools/validate_evidence.py` | visual checks and parameter-snapshot verification |
| `tools/audit_visual_primitives.py` | **new (r2)**; read-only audit of persisted visual evidence against a fresh `collect_primitives()` run |
| `tests/unit/test_visual_structure.py` | **new**, 21 tests |
| `tests/integration/test_phase14_s2.py` | **new**, 11 tests (skipped when the PDFs are absent) |
| `tests/integration/test_phase14_primitive_audit.py` | **new (r2)**, 12 audit/identity/negative tests (skipped when the PDFs are absent) |
| `tests/unit/test_evidence_validation.py` | extended to 40 tests, including one negative case per visual validator code |
| `docs/PHASE1_4_S2A.md` | this report |

## 2. Data model

```text
VisualSegment
  component_id          # RuleComponent that produced the segment
  y0, y1                # span clipped to the table region
  primitive_indices     # page-level collect_primitives() indices

VisualBoundary
  x, role ("outer_left" | "outer_right" | "internal"),
  drawn, coverage (0..1), component_ids, segment_count,
  segments: VisualSegment[]
```

**Index space.**  `primitive_indices` are positions in the list returned by
`collect_primitives(page, page_number, geometry)` — **not**
`RulePrimitive.drawing_index` values.  One drawing can yield zero, one or four
primitives (`quad_edge`), and non-ruling items are skipped, so the two
numberings diverge.  On DS10CP152 page 4, 79 of the 442 primitives already have
`index != drawing_index` (e.g. index 363 is drawing 362, two lines from one
item); resolving an index therefore requires that page's primitive list, which
is exactly what the r2 audit does.

`drawn` has a role-dependent meaning, matching the evidence:

* `internal`: a printed separator exists at this x (it may be partial);
* `outer_left` / `outer_right`: a printed rule covers at least
  `visual_full_height_coverage` of the region height.  A missing or short
  outer rule is *implied* (`drawn = false`) and has no fabricated segment.

`Table` / `DetectedTable` carry:

* `visual_boundaries`: sorted x positions, outer edges always present;
* `visual_boundary_status`: `printed` | `partial` | `implied_outer` |
  `not_printed` | `unknown` (unknown only on tables built outside the detector;
  the validator requires a real status when the run manifest has a parameter
  snapshot);
* `visual_columns`: number of visual columns, `null` for `not_printed`;
* `partial_boundaries`: subset of `visual_boundaries` whose coverage is below
  the full-height threshold;
* `visual_boundary_evidence`: per-boundary coverage/provenance evidence,
  including the segment list above.

Domain invariants enforce the vocabulary, sortedness, `null` columns for
`not_printed`, `visual_columns = len(visual_boundaries) - 1` otherwise, and
`partial_boundaries ⊆ visual_boundaries`.

## 3. Derivation

1. Collect vertical spans from every `RuleComponent` of the region; drop spans
   shorter than `visual_min_rule_span_pt` (4pt); keep spans whose x lies within
   `visual_boundary_tol_pt` (2.5pt) of the region x-range.
2. Sort by `(x, y0, y1, component_id)` and group against an anchor (§3.2).
3. Clip each segment's y-span to the region and compute the union length;
   coverage = union length / region height.
4. Classify groups within tolerance of `bbox.x0` / `bbox.x1` as outer edges;
   strictly interior groups are `internal`.
5. Apply the status rule in §3.1.
6. `visual_columns = len(internal) + 1`; `null` only for `not_printed`.

### 3.1 Status precedence (frozen)

| Condition | Status |
| --- | --- |
| no internal separator | `not_printed` |
| at least one internal separator below full height | `partial` |
| all internals full, both outer edges fully drawn | `printed` |
| all internals full, at least one outer edge not fully drawn | `implied_outer` |

A short or absent outer rule never produces `partial` on its own; `partial` is
driven only by internal separators.  A single implied side is enough for
`implied_outer`, and left/right `drawn`/`coverage` stay separate on their
`VisualBoundary` objects.  If an internal is partial *and* an outer is implied,
`partial` wins.

Synthetic coverage of this table: left drawn/right implied, left implied/right
drawn, both implied, both drawn, short outer only (→ `implied_outer`, no
partial), and internal partial + implied outer (→ `partial`).

### 3.2 Determinism

* Sort key: `(segment.c, segment.a, segment.b, component.component_id)` — total
  order, independent of component iteration or PDF stream order.
* Grouping: the first segment of a group is the anchor; a later segment joins
  only when `abs(segment.c - anchor) <= visual_boundary_tol_pt`.  The group x
  is the mean of its members, computed after the group is complete.
* This removes the running-mean chain effect: segments at
  `100.0, 102.4, 104.4, 106.4` form two groups, not one drifting cluster.  A
  dedicated test asserts that no group spans more than the tolerance from its
  anchor and that shuffling the input yields identical boundaries, coverage,
  `component_ids` and `segment_count`.
* The anchor change did not alter any real-PDF result: across all 430 tables
  of the six runs, `visual_boundaries`, `visual_boundary_status`,
  `visual_columns` and `partial_boundaries` are identical to the first-pass
  runs (0 field diffs).

### 3.3 Evidence sample (real PDF)

`runs/phase14_s2a/review_r1/visual_evidence_sample.json` — DS10CP152 page 4,
table `DS10CP152-P04-T01` (region `[54.15, 101.05, 557.85, 511.45]`, one
component `#0`, status `partial`, 8 visual columns).  Excerpt:

```text
boundary x=346.15 role=internal drawn=true coverage=0.10819
  component_ids=[0] segment_count=1
  segments=[{component_id: 0, y0: 154.0, y1: 198.4,
             primitive_indices: [278, 295]}]
  primitive 278: kind=thin_rect orientation=v a=176.2 b=198.4 c=346.15
                 drawing_index=278 item_index=0 edge_index=0
  primitive 295: kind=thin_rect orientation=v a=154.0 b=176.2 c=346.15
                 drawing_index=295 item_index=0 edge_index=0
```

The union of the two spans is 44.4pt over the 410.4pt region height, so the
recomputed coverage is 0.10819, and the validator classifies it as partial.
`outer_left`/`outer_right` in the same sample have coverage 0.9996, one segment
each, backed by 27 primitives; a `not_printed` or implied-outer boundary instead
has `segments=[]`, `component_ids=[]`, `coverage=0`, and `drawn=false`.

All thresholds live in `TableParams`.  The canonical snapshot is
`json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))`
hashed with SHA-256.  Effective snapshot for every run below:

```text
table_params_sha256 = 82d4df4d1cb3cac9741831b0db36e19fa80c1829abc18b3f8b1ab4ee1c6b9f0a
visual_min_rule_span_pt = 4.0
visual_boundary_tol_pt = 2.5
visual_full_height_coverage = 0.85
```

The FROZEN config SHA is still
`ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c`.

## 4. Evaluator

* Visual predictions come from `Table.visual_columns` /
  `visual_boundary_status`; runs predating S2a fall back to the physical
  `pred_columns` (`visual_tables_without_lattice` records the fallback).
* Visual-column denominator excludes gold `not_printed` items; gold `not_printed`
  items are scored only through `visual_not_printed_pred_null`.
* The logical metric is intentionally unchanged (still physical `pred_columns`)
  because S2b is not authorized.
* Per-item records and CSV expose `pred_visual_columns`, `pred_visual_status`,
  `pred_partial_boundaries`, `visual_exact`, `visual_status_exact`,
  `visual_not_printed_null`.

## 5. Validator

Codes with a dedicated negative test (40 tests in
`tests/unit/test_evidence_validation.py`; the first 13 cover the pre-existing
evidence chain and the rest cover visual/parameter checks):

* lattice shape — `VISUAL_STATUS_MISSING`, `VISUAL_STATUS_INVALID`,
  `VISUAL_BOUNDARIES_UNSORTED`, `VISUAL_BOUNDARY_DUPLICATE`,
  `VISUAL_BOUNDARY_OUTSIDE_TABLE`, `VISUAL_OUTER_LEFT`, `VISUAL_OUTER_RIGHT`,
  `VISUAL_COLUMNS_NOT_NULL`;
* status semantics — `VISUAL_NOT_PRINTED_PARTIAL`,
  `VISUAL_NOT_PRINTED_INTERNAL`, `VISUAL_COLUMNS_MISMATCH`,
  `VISUAL_PARTIAL_EMPTY`, `VISUAL_PARTIAL_NOT_BOUNDARY`,
  `VISUAL_PARTIAL_OUTER`, `VISUAL_PRINTED_OUTER_IMPLIED`,
  `VISUAL_IMPLIED_OUTER_DRAWN`;
* evidence objects — `VISUAL_EVIDENCE_COUNT`, `VISUAL_EVIDENCE_BOUNDARY`,
  `VISUAL_EVIDENCE_ROLE_INVALID`, `VISUAL_EVIDENCE_COVERAGE`,
  `VISUAL_EVIDENCE_ROLE_MISMATCH`, `VISUAL_INTERNAL_NOT_DRAWN`,
  `VISUAL_PARTIAL_COVERAGE`, `VISUAL_FULL_COVERAGE`,
  `VISUAL_OUTER_EVIDENCE_INCONSISTENT`, `VISUAL_NOT_PRINTED_EVIDENCE`;
* segment provenance (r1) — `VISUAL_SEGMENTS_MISSING`,
  `VISUAL_SEGMENT_COUNT`, `VISUAL_COMPONENT_IDS_MISMATCH`,
  `VISUAL_SEGMENT_COMPONENT`, `VISUAL_SEGMENT_SPAN`,
  `VISUAL_SEGMENT_PRIMITIVE`, `VISUAL_COVERAGE_RECOMPUTE`,
  `VISUAL_DRAWN_BELOW_FULL`, `VISUAL_IMPLIED_ABOVE_FULL`.

Run-level checks: `PARAM_SNAPSHOT_HASH` (manifest hash must equal the
recomputed hash of the recorded snapshot), `CONFIG_PARAMS_MISMATCH`
(`run_config.json` must record the same snapshot hash); `MANIFEST_TABLE_COUNT`
and `MANIFEST_CANDIDATE_COUNT` guard the run-level counts.  Thresholds used by
the visual checks are read from the manifest snapshot, not hard-coded.

### 5.1 Independent recomputation (r1)

The validator does not trust any stored aggregate.  For every boundary it:

1. requires a segment list (`VISUAL_SEGMENTS_MISSING`) and checks
   `segment_count` against it (`VISUAL_SEGMENT_COUNT`);
2. checks `component_ids` equals the sorted set of segment component ids
   (`VISUAL_COMPONENT_IDS_MISMATCH`);
3. checks each segment has an integer `component_id` that is listed on the
   boundary (`VISUAL_SEGMENT_COMPONENT`), a non-empty `y0 < y1` span inside the
   table's y-range ± `visual_boundary_tol_pt` (`VISUAL_SEGMENT_SPAN`), and a
   non-empty, ascending, duplicate-free `primitive_indices`
   (`VISUAL_SEGMENT_PRIMITIVE`);
4. clips the recorded segment spans to the table height, unions them, divides by
   the height, and compares with the stored `coverage` at 1e-6
   (`VISUAL_COVERAGE_RECOMPUTE`).  This is computed from the recorded geometry
   alone; a wrong `coverage` and a matching wrong evidence coverage cannot both
   pass;
5. cross-checks `drawn` against the recomputed coverage
   (`VISUAL_DRAWN_BELOW_FULL` for a drawn non-internal boundary below the full
   threshold, `VISUAL_IMPLIED_ABOVE_FULL` for an implied boundary above it).
   Internal boundaries are exempt from the full-height rule for `drawn`
   because their `drawn` means "a printed separator exists", not "covers the
   full height".

The primitive indices themselves are checked for shape only; the validator does
not re-open the PDF, so it validates the recorded evidence chain rather than
re-parsing.  Integration tests
(`test_visual_evidence_traces_to_components_and_primitives`) re-derive coverage
from the emitted segments on real PDFs.

### 5.2 Independent primitive audit (r2, outside the validator)

`tools/audit_visual_primitives.py` is a separate read-only audit; the formal
validator and the visual algorithm are unchanged.  It has three independent
stages.

**Identity gate (P1, P4).** Before touching boundaries it verifies the run
directory against its own record and refuses with `AuditIdentityError` (CLI exit
status 2) on any mismatch:

* the manifest `artifacts` list must contain every required artifact
  (`document.json`, `pages/geometry.json`, `tables.json`, `run_config.json`);
  a missing entry is a refusal, never a skipped file;
* each required artifact's SHA-256 equals its manifest entry;
* `source.pdf` SHA-256 equals both `run_manifest.json:document_sha256` and
  `document.json:sha256` (a wrong-version PDF of the same product is refused);
* `page_count`, `dpi`, page sizes and rotations agree between the manifest,
  `document.json`, the recorded geometry and a fresh `load_pdf(dpi=<manifest>)`;
* every recorded page's CropBox, MediaBox, display rect and rotation equals the
  fresh PDF's geometry contract;
* `run_config.json` and `run_manifest.json` carry the same `table_params`
  snapshot, the same `table_params_sha256`, and the same
  `parser_config_sha256`; the snapshot hash is recomputed with
  `snapshot_sha256()` rather than trusted.

The audit then builds `TableParams(**snapshot["params"])` and uses those values
for every clip/coverage/threshold decision — no visual parameter is hard-coded.

**Component-rebuild tolerance (P4-1).** `GRID_TOL = 2.5` is an S1 code constant
in `src/icpdf/parser/rule_primitives.py`, not a `TableParams` field, so it is not
covered by `table_params_sha256`.  The audit does not define its own tolerance:
it imports that symbol and passes it to `build_components(tol=GRID_TOL)`, and it
verifies that both `build_components` and `rule_components` still default to the
same value.  The `identity.grid_tol` block records the symbol, value, source file
of the S1 module, its SHA-256, both defaults, and
`in_table_params = false` / `covered_by_table_params_sha256 = false`, so a
reviewer can see exactly what is and is not snapshot-bound.  A drift between the
constant and the S1 defaults refuses the audit.

**Independent rebuild (P2).** It re-opens the page and re-runs the S1 chain
`collect_primitives(page, page_number, geometry)` →
`build_components(..., tol=GRID_TOL, min_width=params.rule_min_width_pt,
min_height=params.rule_min_height_pt)`.  The resulting components are the only
ones accepted: every segment's `component_id` must resolve in that fresh set,
must be listed on the boundary and in `region_components`, its bbox must
contain the boundary x and the segment y-span, and it must own a vertical
ruling at that x.  Membership is checked against
`component.primitive_indices`, not against a recorded component list.  The
audit JSON exposes the rebuilt primitive count, component count and the
bbox/primitive/vertical counts of every component it actually used.

**Primitive resolution (P3).** For each segment and raw primitive it checks:
page, `orientation == "v"`, `abs(primitive.c - boundary.x) <=
params.visual_boundary_tol_pt`, membership in the rebuilt component, and
non-duplication across the boundary.  Each primitive span is clipped to the
table height; then:

* `y0_stored == min(clipped starts)` and `y1_stored == max(clipped ends)`
  (`SEGMENT_SPAN_MISMATCH`);
* coverage is recomputed from the union of **raw primitive** spans divided by
  the table height (`COVERAGE_MISMATCH`), never from the recorded segment
  geometry;
* stored `component_ids` must equal the segment component set
  (`COMPONENT_IDS_MISMATCH`); implied outers must carry no segments.

Issue codes include `SEGMENT_COUNT_MISMATCH`, `COMPONENT_MISSING`,
`COMPONENT_NOT_IN_REGION`, `COMPONENT_BBOX_MISMATCH`,
`COMPONENT_VERTICAL_MISSING`, `PRIMITIVE_INDEX_OUT_OF_RANGE`,
`PRIMITIVE_INDEX_UNSORTED`, `PRIMITIVE_DUPLICATE_IN_BOUNDARY`,
`PRIMITIVE_NOT_VERTICAL`, `PRIMITIVE_X_MISMATCH`,
`PRIMITIVE_NOT_IN_COMPONENT`, `PRIMITIVE_OUTSIDE_SEGMENT`,
`SEGMENT_SPAN_MISMATCH`, `COVERAGE_MISMATCH`, `DRAWN_WITHOUT_SEGMENTS`,
`DRAWN_BELOW_FULL`, `IMPLIED_WITH_SEGMENTS`.

It can audit either an in-memory `DetectedTable` (integration tests) or the
persisted `tables.json` of a frozen run:

```text
python -m tools.audit_visual_primitives --run <run dir> \
  --gold gold/generalization/gold_table_set.jsonl \
  --item-id DS10CP152-P04-T01 --out <audit.json>
```

Exit status is 0 when clean, 1 when issues are found, and 2 when identity
verification refuses the run.  The emitted JSON has `identity` (document and
parameter hashes, DPI, artifacts), `rebuild` (fresh primitive/component
counts), per-boundary `recomputed_coverage`, and per-segment
`recomputed_y0`/`recomputed_y1`.  The audit never writes into a run directory;
`--out` is explicit.

## 6. Tests

```text
python -m pytest
158 passed, 2 xfailed in 12.07s
```

Per-file counts: `tests/unit/test_visual_structure.py` (21),
`tests/integration/test_phase14_s2.py` (11),
`tests/integration/test_phase14_primitive_audit.py` (12), and
`tests/unit/test_evidence_validation.py` (40, one negative case per validator
code).  The other 74 tests are unchanged.

The synthetic suite covers the status table explicitly: left drawn/right
implied, left implied/right drawn, both implied, both drawn, a short outer rule
with full internals (→ `implied_outer`, never `partial`), and an internal
partial combined with an implied outer (→ `partial`).  It also covers
order-independent grouping, anchor-based chain prevention
(`100.0, 102.4, 104.4, 106.4` → two groups), segment→component→primitive
linkage, and the rule that an implied outer carries no fabricated segment.

The integration cases assert the required real-PDF outcomes: MICRF103 P03
`implied_outer` with six columns and both outer edges undrawn; DS10CP152 P04/P05
`partial` 8; CY29FCT520 P04-T01 `printed` 4; CY29 P05/P06 partial boundaries;
DS10 P11 and CY29 P08 `not_printed` with `null` columns; DS10 P13-T02
headerless; CY29 P10 package outline vs the nested dimension table
(maximum-IoU matching).  Two r1 cases additionally recompute coverage from the
emitted segments on DS10 P04-T01 and prove that MICRF103 P03's implied outers
carry no segment, `component_ids=[]` and `coverage=0`.

The r2 audit file adds the three required samples: DS10CP152 P04 internal
partial (9 boundaries, primitive-level coverage 0.108187 reproduced),
MICRF103 P03 implied outer (no primitive backing at either outer edge), and
CY29FCT520 P05 multiple partials (0.555596 reproduced from raw primitives).  It
also proves the primitive index space is `collect_primitives` order rather than
`drawing_index`, and includes negative cases for an out-of-range index, a
horizontal primitive, a stretched/shifted segment span, and a drawn outer with
no segments.

## 7. Runs

Review-round r1 runs, frozen after this report.  The earlier
`final_phase12/` / `final_generalization/` runs had no segment evidence and are
superseded; they remain on disk only for the first-pass comparison in §3.2.

| Document | Run | Tables | Candidates | Manifest SHA-256 |
| --- | --- | --- | --- | --- |
| LM358 | `runs/phase14_s2a/review_r1/final_phase12/20261106T023448Z-f5c3cc` | 40 | 5641 | `fe812c0b724552fe5d8511fc0ece81d11e27db4260908168a3ac5edca5d78a62` |
| ADS1299 | `runs/phase14_s2a/review_r1/final_phase12/20261106T023504Z-e757dc` | 57 | 2661 | `ef193014adfeaeec4845de58ca990ef12c79ef399835e5934dfe90b812a9df6d` |
| ADC12DJ5200 | `runs/phase14_s2a/review_r1/final_phase12/20261106T023521Z-c36d7b` | 301 | 9328 | `17f43934ce010a4d56bb64a46eb43b2355476c5aec3ccf5967484e953f6e1e7e` |
| MICRF103 | `runs/phase14_s2a/review_r1/final_generalization/20261106T023642Z-d90030` | 4 | 146 | `a7600f1f9b698578f8528c37e83853be8bb582dbc8a025d646f8f43b250b6486` |
| DS10CP152 | `runs/phase14_s2a/review_r1/final_generalization/20261106T023643Z-7f25c1` | 14 | 533 | `2281de79f3c55a9c79c4409f75d1dbcddd7650fc5711b52a450baf55f585e420` |
| CY29FCT520 | `runs/phase14_s2a/review_r1/final_generalization/20261106T023646Z-506c4e` | 14 | 590 | `c708846c3094e100ba24d644c4f75318e78d805520b32958ca6508e8bb18a241` |

Table/candidate counts equal the S1 final runs exactly.  Every manifest reports
`table_params_sha256=82d4df4d…` and the frozen parser config SHA.

### 7.1 Evidence validator

`python -m tools.validate_evidence --run <dir> --strict --json
<dir>/validator_report.json` on all six review-r1 runs (exit status 0):

| Run | errors | warnings | visual status counts |
| --- | --- | --- | --- |
| LM358 | 0 | 0 | printed 16, partial 12, not_printed 12 |
| ADS1299 | 0 | 0 | printed 43, partial 7, not_printed 7 |
| ADC12DJ5200 | 0 | 0 | printed 198, partial 75, not_printed 28 |
| MICRF103 | 0 | 0 | printed 2, implied_outer 1, partial 1 |
| DS10CP152 | 0 | 0 | printed 9, partial 2, not_printed 3 |
| CY29FCT520 | 0 | 0 | printed 7, partial 4, not_printed 3 |

This includes the independent segment→coverage recomputation added in r1; every
stored coverage and every outer `drawn` flag is reproduced from the recorded
segments.

### 7.2 Gold v2 (`gen-2026-11-06.2`, 21 items)

Command: `python -m tools.goldset.evaluate --gold gold/generalization/gold_table_set.jsonl
--run <three review-r1 generalization runs> --label phase14-s2a-review-r1
--json runs/phase14_s2a/review_r1/generalization_report.json`.

| Metric | Value |
| --- | --- |
| Detection | TP 21, FP 4, FN 0 (precision 0.84, recall 1.0, F1 0.913) |
| Visual columns exact | **19 / 19** comparable items |
| `not_printed` predicted null | **2 / 2** |
| Visual status exact | 18 / 19 |
| Logical columns exact | 18 / 21 (identical to S1) |
| Row count exact | 21 / 21 |

Per item:

| item | gold visual | pred visual | gold status | pred status | pred partial x |
| --- | --- | --- | --- | --- | --- |
| CY29FCT520-P04-T01 | 4 | 4 | printed | printed | – |
| CY29FCT520-P04-T02 | 6 | 6 | partial | partial | 173.2 |
| CY29FCT520-P05-T01 | 7 | 7 | partial | partial | 193.9, 266.0 |
| CY29FCT520-P06-T01 | 5 | 5 | partial | partial | 290.2 |
| CY29FCT520-P08-T01 | null | null | not_printed | not_printed | – |
| CY29FCT520-P10-T01 | 3 | 3 | printed | printed | – |
| DS10CP152-P02-T01 | 4 | 4 | printed | printed | – |
| DS10CP152-P03-T01 | 2 | 2 | **partial** | **printed** | – |
| DS10CP152-P03-T02 | 5 | 5 | printed | printed | – |
| DS10CP152-P04-T01 | 8 | 8 | partial | partial | 346.1 |
| DS10CP152-P05-T01 | 8 | 8 | partial | partial | 363.1 |
| DS10CP152-P07-T01 | 4 | 4 | printed | printed | – |
| DS10CP152-P07-T02 | 4 | 4 | printed | printed | – |
| DS10CP152-P11-T01 | null | null | not_printed | not_printed | – |
| DS10CP152-P13-T01 | 13 | 13 | printed | printed | – |
| DS10CP152-P13-T02 | 2 | 2 | printed | printed | – |
| DS10CP152-P14-T01 | 8 | 8 | printed | printed | – |
| DS10CP152-P15-T01 | 9 | 9 | printed | printed | – |
| MICRF103-P01-T01 | 3 | 3 | printed | printed | – |
| MICRF103-P02-T01 | 3 | 3 | printed | printed | – |
| MICRF103-P03-T01 | 6 | 6 | implied_outer | implied_outer | – |

### 7.3 Phase 1.2 (46 items)

Command: same evaluator against `gold/gold_table_set.jsonl` with the three
review-r1 Phase 1.2 runs (`--label phase14-s2a-review-r1-phase12
--json runs/phase14_s2a/review_r1/phase12_report.json`).  Detection stays
TP 46 / FP 0 / FN 0.  All physical metrics (rows, cell text, headers, roles,
table type) are byte-identical to the S1 control run; see §8.

Phase 1.2 gold is `gold-2026-11-06.1` and has **no visual annotations**.  The
evaluator therefore falls back to the physical column count as a stand-in
(diagnostic only, status defaults to `printed`); S2a scores 36/46 on that
stand-in versus 44/46 for the S1 legacy fallback, because derived visual
columns legitimately differ from the physical grid where the structure layer
split on header midpoints.  This is **not** an S2a acceptance metric; the
authorized visual metric is §7.2 (19/19).  Examples: LM358 P05-T01 has five
physical columns but four drawn visual separators; ADC12DJ5200 P98/P100 and
ADS1299 P76 have no internal vertical ruling (`not_printed`) although the
structure layer recovered columns from text alignment.

### 7.4 Primitive authenticity audit (r2)

`python -m tools.audit_visual_primitives --run <review-r1 run> --gold
gold/generalization/gold_table_set.jsonl --item-id <id> --out
runs/phase14_s2a/review_r2/audit_<item>.json`:

| Sample | Table | Page | Status | Boundaries | Result |
| --- | --- | --- | --- | --- | --- |
| DS10CP152 | `DS10CP152-P04-T01` | 4 | partial | 9 | **0 issues**; internal x=346.15 recomputes 0.108187 from primitives 278+295 |
| MICRF103 | `MICRF103-P03-T01` | 3 | implied_outer | 7 | **0 issues**; both outers have 0 segments / 0 primitives, raw coverage 0 |
| CY29FCT520 | `CY29FCT520-P05-T01` | 5 | partial | 8 | **0 issues**; partials 193.946 / 265.958 recompute 0.555596 from raw primitives |

Primitive index space on those pages: DS10 page 4 has 442 primitives, 79 with
`index != drawing_index`; MICRF103 page 3 has 58 / 23; CY29FCT520 page 5 has
334 / 333.  This confirms the evidence indices cannot be treated as
`drawing_index`.

Every audit also re-verified the run identity before evaluating boundaries:

| Sample | `document_sha256` | `table_params_sha256` | DPI | Rebuilt primitives / components |
| --- | --- | --- | --- | --- |
| MICRF103 P03 | `670a1fab…a6708` | `82d4df4d…6b9f0a` | 150 | 58 / 5 |
| DS10CP152 P04 | `14f395e4…30fb82` | `82d4df4d…6b9f0a` | 150 | 442 / 1 |
| CY29FCT520 P05 | `5f374e76…80686c` | `82d4df4d…6b9f0a` | 150 | 334 / 1 |

Each stored segment `[y0, y1]` equals the min/max of its raw primitives clipped
to the table, and each recomputed coverage equals the stored value exactly
(delta 0.0).

Negative controls (integration tests) inject a tampered primitive index
(out-of-range and a horizontal primitive), tampered segment spans (stretched
and shifted), a duplicated primitive inside one boundary, and a primitive
reassigned to a different component; the audit rejects each with the expected
code.  A faked drawn outer with no segments is also rejected.  A run whose
`source.pdf` is a different document of the same product family is refused by
the identity gate before any boundary is read.

## 8. Physical-structure diff evidence

Two artifacts under `runs/phase14_s2a/review_r1/`:

* `physical_diff.json` — S1 final run vs S2a run for **all** 430 tables and
  **18,899** candidates, comparing bbox, page, rows/cells, `detection_method`,
  `region_components`, `boundary_source`, `reconstruction_status`,
  `confidence`, headers/header_path, and (candidates) `candidate_id`,
  `cell_id`, `table_id`, bbox, `raw_text`, `column_role`, role provenance.
  Result: **0 table diffs, 0 candidate diffs**.
* `gold_item_diff.json` — per gold item, S1 and S2a predictions matched by
  maximum IoU (≥0.5), then compared field by field.  Result: **67 / 67 gold
  items matched, 0 field diffs** (Phase 1.2: 46/46; Gold v2: 21/21).

Evaluator control comparison (`s1_*_control.json` vs the r1 reports): every
overlapping non-visual metric is identical; the only differences are the new
visual keys, the label and the generation timestamp.

## 9. Known divergence (reported, not hidden)

`DS10CP152-P03-T01` (Absolute Maximum Ratings, headerless two-column list):

* gold: `partial`, `partial_boundaries = [331.0]`;
* S2a: `printed`, boundary x = 331.05, measured coverage **0.952**
  (two segments, 1 component), threshold 0.85;
* visual columns agree (2 = 2), so the case counts as a visual-column exact
  match and as a visual-status mismatch (18/19).

Gold notes that the centre rule "spans only some row bands"; the rule does
have a visible gap, but it is small relative to the table height.  Lowering
the threshold below 0.952 would also reclassify MICRF103 P03 (coverage 0.881,
must stay full-height for `implied_outer`), so no threshold separates the two
cases.  The divergence is left visible for the Reviewer rather than tuned
against the frozen gold.

Minor coordinate note: CY29FCT520-P06-T01 partial boundary x = 290.2 vs gold
289.8 (0.4pt, inside the 2.5pt tolerance); the count and status agree.

## 10. Not done / not claimed

* No S2b: no logical boundary lattice, no logical projection, logical metric
  unchanged.
* No S2c: no `ConditionContext`, no `ConditionBand`.
* No change to `grid.xs` / `grid.ys`, physical cell bbox/text or Candidate IDs.
* No change to gold v1/v2, the Candidate Registry, or the existing validator
  checks.
* Parameter values are the approved defaults; no LLM or automatic parameter
  generation was used.
* r2 adds only a read-only audit tool and integration tests; the parser,
  visual algorithm and `tools/validate_evidence.py` are unchanged.
* This document is an evidence bundle for independent review; S2a is **not**
  declared passed here.

## 11. Reviewer traceability

| Item | Resolution | Code | Tests | Evidence |
| --- | --- | --- | --- | --- |
| P1 status precedence | Frozen four-row rule; outer deficit never yields `partial` | `parser/visual_structure.py` status block; docstring | 6 status-combination tests in `test_visual_structure.py` | §3.1; Gold v2 status 18/19 |
| P2 evidence provenance | `segments` per boundary with `component_id`, clipped span, `primitive_indices`; implied outer has no segment | `domain/visual.py`, `parser/visual_structure.py` | `test_segment_evidence_links_components_and_primitives`, `test_implied_outer_has_no_fabricated_segment`; 2 integration cases | §3.3 real sample; `review_r1/visual_evidence_sample.json` |
| Validator independence | Recomputes coverage from recorded segment geometry and re-checks outer `drawn`; never trusts the stored aggregate | `tools/validate_evidence.py` (`_validate_visual_segments`) | 9 new negative tests | §5.1; six runs 0 errors / 0 warnings |
| P3 determinism | Total sort order + fixed-anchor grouping, group mean computed after close | `_group_segments` | `test_grouping_is_order_independent`, `test_anchor_grouping_prevents_chain_merge` | §3.2; zero visual-field diffs vs first pass |
| Primitive authenticity (r2) | Reopen PDF, re-run `collect_primitives`, resolve indices, check ownership/orientation/x/span, recompute coverage, tamper negatives | `tools/audit_visual_primitives.py` | `test_phase14_primitive_audit.py` (11) | §5.2, §7.4; 3 samples 0 issues |
| Index space (r2) | `primitive_indices` = `collect_primitives` position, not `drawing_index` | docstring + audit | index-space test | §2; DS10 79/442 differ |
| r2-P1 PDF identity | Source SHA-256, artifact hashes, page count/DPI, page sizes, CropBox, rotation and display rect all checked against the manifest before any boundary is read; wrong-version PDF refused | `verify_identity`, `AuditIdentityError` | `test_run_identity_matches_spec_and_manifest`, `test_wrong_version_pdf_is_refused` | §5.2 gate; §7.4 identity table |
| r2-P2 component rebuild | Fresh `build_components()` is the only accepted component set; bbox, vertical ruling and primitive ownership checked against it | `verify_identity` + `build_components()` call, `COMPONENT_*` codes | 3 sample audits + `test_cross_component_primitive_reference_fails_the_audit` | §5.2 rebuild block in every `audit_*.json` |
| r2-P3 strict segment rebuild | `y0 = min(clipped starts)`, `y1 = max(clipped ends)`, coverage from raw primitive union; duplicate/cross-component references rejected | `audit_table`, `_segment_spans` | `test_tampered_segment_span_fails_the_audit`, `test_duplicate_primitive_in_one_boundary_fails_the_audit` | §7.4 zero deltas; per-segment recomputed values |
| r2-P4 snapshot binding | Thresholds come from `manifest.table_params`; snapshot SHA recomputed with `snapshot_sha256()`; no visual-threshold literal in the audit tool | `verify_identity`, `TableParams(**snapshot["params"])` | identity tests | §5.2 gate; `identity.table_params_sha256` |
| r2-P4-1 `GRID_TOL` | 2.5 from `rule_primitives.GRID_TOL`; not in `TableParams` / snapshot (recorded as false); audit imports the S1 symbol, checks both S1 defaults still equal it, and records source file SHA-256 | `grid_tol_binding`, component rebuild call | identity test asserts value/defaults/`in_table_params` | §5.2; `identity.grid_tol` |
| r2-P4-2 artifact completeness | Required set is checked before hashing; a manifest that omits any required artifact is refused, not skipped | `REQUIRED_ARTIFACTS`, `verify_identity` | `test_manifest_missing_required_artifact_is_refused` | §5.2; error `manifest does not record artifact …` |
| DS10CP152-P03-T01 | Kept as reported known limitation; thresholds untouched | – | – | §9 |
| Scope boundaries | Gold v1/v2, S1 physical rules, thresholds, S2b/S2c all untouched; no Codeup push | – | – | §10 |

Acceptance remains with the Reviewer.  This round supplies the requested code
diff, supplementary tests, validator results and this updated report; it does
not self-declare S2a passed.
