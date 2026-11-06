# Phase 1.4 S2a — VisualBoundary (visual boundary lattice)

Status: implementation slice S2a complete, local commit only, **awaiting
Reviewer**.  S2b (logical boundary / logical projection) and S2c
(`ConditionContext`) are not started.  No acceptance is self-declared.

Scope actually delivered, per the S2a authorization:

* visual boundary derivation from printed vertical ruling, attached to
  `DetectedTable` and the domain `Table`;
* visual fields in the gold evaluator (separate denominator, legacy fallback
  for Gold v1);
* visual invariants in `tools/validate_evidence.py`;
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
| `src/icpdf/domain/visual.py` | **new**; frozen `VisualBoundary` (`x`, `role`, `drawn`, `coverage`, `component_ids`, `segment_count`) and the role/status vocabularies |
| `src/icpdf/parser/visual_structure.py` | **new**; `VisualStructure` and `build_visual_structure(region, params)` |
| `src/icpdf/parser/config.py` | `visual_min_rule_span_pt=4.0`, `visual_boundary_tol_pt=2.5`, `visual_full_height_coverage=0.85`; `table_params_snapshot`, `snapshot_sha256`, `table_params_sha256` |
| `src/icpdf/parser/table_detector.py` | `DetectedTable` additive fields `visual_boundaries`, `visual_boundary_status`, `visual_columns`, `partial_boundaries`, `visual_boundary_evidence`; builds them per accepted region |
| `src/icpdf/domain/table.py` | matching additive fields on `Table` + invariants |
| `src/icpdf/parser/table_rebuilder.py` | copies the five visual fields into `Table` |
| `src/icpdf/parser/pipeline.py` | writes `table_params` and `table_params_sha256` into both `run_config.json` and `run_manifest.json` |
| `tools/goldset/evaluate.py` | visual prediction/status metrics, separate denominator, legacy fallback, CSV columns, Markdown rows |
| `tools/validate_evidence.py` | visual checks and parameter-snapshot verification |
| `tests/unit/test_visual_structure.py` | **new**, 13 tests |
| `tests/integration/test_phase14_s2.py` | **new**, 9 tests (skipped when the PDFs are absent) |
| `tests/unit/test_evidence_validation.py` | extended to 31 tests, including one negative case per visual validator code |
| `docs/PHASE1_4_S2A.md` | this report |

## 2. Data model

```text
VisualBoundary
  x, role ("outer_left" | "outer_right" | "internal"),
  drawn, coverage (0..1), component_ids, segment_count
```

`Table` / `DetectedTable` carry:

* `visual_boundaries`: sorted x positions, outer edges always present;
* `visual_boundary_status`: `printed` | `partial` | `implied_outer` |
  `not_printed` | `unknown` (unknown only on tables built outside the detector;
  the validator requires a real status when the run manifest has a parameter
  snapshot);
* `visual_columns`: number of visual columns, `null` for `not_printed`;
* `partial_boundaries`: subset of `visual_boundaries` whose coverage is below
  the full-height threshold;
* `visual_boundary_evidence`: per-boundary coverage/provenance evidence.

Domain invariants enforce the vocabulary, sortedness, `null` columns for
`not_printed`, `visual_columns = len(visual_boundaries) - 1` otherwise, and
`partial_boundaries ⊆ visual_boundaries`.

## 3. Derivation

1. Collect vertical spans from every `RuleComponent` of the region; drop spans
   shorter than `visual_min_rule_span_pt` (4pt); keep spans whose x lies within
   `visual_boundary_tol_pt` (2.5pt) of the region x-range.
2. Group collinear segments whose x is within tolerance of the running group
   mean; the group x is the mean.
3. Clip each segment's y-span to the region and compute the union length;
   coverage = union length / region height.
4. Classify groups within tolerance of `bbox.x0` / `bbox.x1` as outer edges;
   strictly interior groups are `internal`.
5. Status precedence: `not_printed` (no internal boundary at all) → `partial`
   (any internal or outer coverage below `visual_full_height_coverage`) →
   `implied_outer` (any single outer edge not fully drawn) → `printed`.
   A single-sided implied outer follows the Reviewer rule: it is
   `implied_outer`, and the left/right evidence is kept separately on the
   `VisualBoundary` objects rather than collapsed.
6. `visual_columns = len(internal) + 1`; `null` only for `not_printed`.

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

New codes (one negative test each):

`VISUAL_STATUS_MISSING`, `VISUAL_STATUS_INVALID`, `VISUAL_BOUNDARIES_UNSORTED`,
`VISUAL_BOUNDARY_DUPLICATE`, `VISUAL_BOUNDARY_OUTSIDE_TABLE`,
`VISUAL_OUTER_LEFT`, `VISUAL_OUTER_RIGHT`, `VISUAL_COLUMNS_NOT_NULL`,
`VISUAL_NOT_PRINTED_PARTIAL`, `VISUAL_NOT_PRINTED_INTERNAL`,
`VISUAL_COLUMNS_MISMATCH`, `VISUAL_PARTIAL_EMPTY`,
`VISUAL_PARTIAL_NOT_BOUNDARY`, `VISUAL_PARTIAL_OUTER`,
`VISUAL_EVIDENCE_COUNT`, `VISUAL_EVIDENCE_BOUNDARY`,
`VISUAL_EVIDENCE_ROLE_INVALID`, `VISUAL_EVIDENCE_COVERAGE`,
`VISUAL_EVIDENCE_ROLE_MISMATCH`, `VISUAL_INTERNAL_NOT_DRAWN`,
`VISUAL_PARTIAL_COVERAGE`, `VISUAL_FULL_COVERAGE`,
`VISUAL_OUTER_EVIDENCE_INCONSISTENT`, `VISUAL_NOT_PRINTED_EVIDENCE`,
`VISUAL_PRINTED_OUTER_IMPLIED`, `VISUAL_IMPLIED_OUTER_DRAWN`.

Run-level checks: `PARAM_SNAPSHOT_HASH` (manifest hash must equal the
recomputed hash of the recorded snapshot) and `CONFIG_PARAMS_MISMATCH`
(`run_config.json` must record the same snapshot hash).  Thresholds used by
the visual checks are read from the manifest snapshot, not hard-coded.

## 6. Tests

```text
python -m pytest
127 passed, 2 xfailed in 13.44s
```

New: `tests/unit/test_visual_structure.py` (13) and
`tests/integration/test_phase14_s2.py` (9).  The integration cases assert the
required real-PDF outcomes: MICRF103 P03 `implied_outer` with six columns and
both outer edges undrawn; DS10CP152 P04/P05 `partial` 8; CY29FCT520 P04-T01
`printed` 4; CY29 P05/P06 partial boundaries; DS10 P11 and CY29 P08
`not_printed` with `null` columns; DS10 P13-T02 headerless; CY29 P10 package
outline vs the nested dimension table (maximum-IoU matching).

## 7. Runs

Fresh run directories, frozen after this report:

| Document | Run | Tables | Candidates | Manifest SHA-256 |
| --- | --- | --- | --- | --- |
| LM358 | `runs/phase14_s2a/final_phase12/20261106T022039Z-f28c83` | 40 | 5641 | `f36796fee24ec6d324519f78221ed1e7494241817e8a6915c131ec152504a13e` |
| ADS1299 | `runs/phase14_s2a/final_phase12/20261106T022056Z-775fab` | 57 | 2661 | `10733f135ea7086e0f9f49d965755f75cc4ba4260752701a7974396e12fcad0a` |
| ADC12DJ5200 | `runs/phase14_s2a/final_phase12/20261106T022114Z-0a7240` | 301 | 9328 | `35a281a91ce30a18031c4ea2da62774d725d08e52b6f352397cce7368efa59ef` |
| MICRF103 | `runs/phase14_s2a/final_generalization/20261106T022234Z-3ddfe2` | 4 | 146 | `ee1e9899fac2a9a01a5431664d3905230de53654a11c5ecee291c892f1fd8246` |
| DS10CP152 | `runs/phase14_s2a/final_generalization/20261106T022235Z-797437` | 14 | 533 | `caaa844ee2bb5a2103102547118a3efd64095bf5f18a67e2edce43fe573ba4f0` |
| CY29FCT520 | `runs/phase14_s2a/final_generalization/20261106T022238Z-736443` | 14 | 590 | `51d58596df27d0949e086cd0b44fa3e0aeeeeb2fdde6444961dc61557ffffa9e` |

Table/candidate counts equal the S1 final runs exactly.

### 7.1 Evidence validator

`python -m tools.validate_evidence --run <dir> --strict` on all six:

| Run | errors | warnings | visual status counts |
| --- | --- | --- | --- |
| LM358 | 0 | 0 | printed 16, partial 12, not_printed 12 |
| ADS1299 | 0 | 0 | printed 43, partial 7, not_printed 7 |
| ADC12DJ5200 | 0 | 0 | printed 198, partial 75, not_printed 28 |
| MICRF103 | 0 | 0 | printed 2, implied_outer 1, partial 1 |
| DS10CP152 | 0 | 0 | printed 9, partial 2, not_printed 3 |
| CY29FCT520 | 0 | 0 | printed 7, partial 4, not_printed 3 |

All runs report `table_params_sha256=82d4df4d…` and the same frozen parser
config SHA.

### 7.2 Gold v2 (`gen-2026-11-06.2`, 21 items)

Command: `python -m tools.goldset.evaluate --gold gold/generalization/gold_table_set.jsonl
--run <three S2a generalization runs> --label phase14-s2a-generalization
--json runs/phase14_s2a/generalization_report.json`.

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

Command: same evaluator against `gold/gold_table_set.jsonl` with the three S2a
Phase 1.2 runs.  Detection stays TP 46 / FP 0 / FN 0.  All physical metrics
(rows, cell text, headers, roles, table type) are byte-identical to the S1
control run; see §8.

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

## 8. Physical-structure diff evidence

Two artifacts under `runs/phase14_s2a/`:

* `physical_diff.json` — S1 final run vs S2a run for **all** 430 tables and
  **18,899** candidates, comparing bbox, page, rows/cells, `detection_method`,
  `region_components`, `boundary_source`, `reconstruction_status`,
  `confidence`, headers/header_path, and (candidates) `candidate_id`,
  `cell_id`, `table_id`, bbox, `raw_text`, `column_role`, role provenance.
  Result: **0 table diffs, 0 candidate diffs**.
* `gold_item_diff.json` — per gold item, S1 and S2a predictions matched by
  maximum IoU (≥0.5), then compared field by field.  Result: **67 / 67 gold
  items matched, 0 field diffs** (Phase 1.2: 46/46; Gold v2: 21/21).

Evaluator control comparison (`s1_*_control.json` vs the S2a reports): every
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
* This document is an evidence bundle for independent review; S2a is **not**
  declared passed here.
