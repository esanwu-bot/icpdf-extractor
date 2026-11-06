# HANDOFF

## Round 1 — Phase 0 (2026-11-05)

**Status:** complete. No PDF parsing or LLM code was written, by design.

### Delivered

- Project skeleton at `E:\workspace\icpdf-extractor` (new, empty at start; no
  code copied or imported from the old IcPdfParser).
- `pyproject.toml` (Python >=3.12, pydantic v2, pymupdf, typer, rich,
  python-dotenv, pillow; dev: pytest).
- `configs/parser.yaml`, `configs/extraction.yaml`.
- Domain models (`src/icpdf/domain/`):
  - `Document` (sha256 identity, page sizes/rotations, tz-aware created_at);
  - `Product` (requested vs normalized MPN kept separate; evidence required on mismatch);
  - `Table` / `TableRow` / `Cell` (page ranges, unique IDs, unresolved reason);
  - `Candidate` / `CandidateSet` (table/row/cell/page/bbox binding, unique IDs,
    single-document set);
  - `Evidence` (document sha256 + page + bbox + raw text);
  - `Parameter` / `FormalParameterSet` (formal status requires evidence;
    unresolved requires a reason; formal set rejects non-formal rows).
- Docs: `DATA_CONTRACT.md`, `ARCHITECTURE.md`, `MVP_ROADMAP.md`, `DECISIONS.md`.
- CLI skeleton (`src/icpdf/cli.py`): `init` implemented; parse/render/tables/
  candidates/extract/report declared as Phase 1/2 placeholders.
- Placeholder packages for `parser/`, `extraction/`, `audit/`, `storage/`.

### Tests

```text
python -m pytest
24 passed in 0.69s
```

Negative cases covered: bad SHA, naive datetime, partial page sizes, MPN
overwrite without evidence, duplicate cell IDs, cell page outside table range,
unresolved table without reason, bbox order, blank candidate text, duplicate
candidate IDs, cross-document candidates, formal parameter without evidence,
unresolved parameter without reason, formal set accepting unresolved rows.

### Open items

1. Rotation semantics for bboxes must be fixed in Phase 1 (pre- vs post-rotation).
2. `Evidence` currently requires table/row/cell IDs; paragraph-level evidence
   needs a contract version bump when Phase 2 adds prose extraction.
3. No schema version field on individual objects yet; planned at artifact level
   (`run_manifest.json`) in Phase 1.
4. Typer/Rich/dotenv are declared but not exercised in Phase 0 tests.

### Next round (Phase 1)

1. PDF loader (sha256, page count/sizes/rotations, encrypted/corrupt detection).
2. Page renderer (PNG at configurable DPI, page↔pixel mapping).
3. Text blocks (block/line/span/word, all bbox).
4. Table detector (vector lines + alignment; emit uncertainty reasons).
5. Table rebuilder (rows/columns/headers/cells; unresolved when unprovable).
6. Candidate registry (immutable, bound to table/row/cell/page/bbox).
7. Synthetic PDF fixtures + the duplicate-value-in-two-tables proof.

---

## Round 2 — Phase 1 (2026-11-05)

**Status:** complete for the MVP parser scope.

### Delivered

- Contract amendments approved before coding:
  - coordinate semantics frozen: bbox space = `page.rect` (post-crop, post-rotate),
    origin top-left, unit = point; PNG mapping = `zoom = dpi/72` with `PageGeometry`;
  - `Evidence` base fields required, table/row/cell IDs optional except for
    `cell_text` / `table_row`;
  - `Candidate` gained `extraction_method`, `source_text_type`, `reconstruction_status`;
  - docs state that evidence presence is not verification; audit must check
    document/table/row/cell/value/unit/applicable-MPN associations.
- `parser/coords.py`: `PageGeometry` + point↔pixel round-trip.
- `parser/pdf_loader.py`: sha256 identity, page geometry, encrypted/corrupt rejection.
- `parser/page_renderer.py`: PNG at configured DPI (integer DPI required by PyMuPDF 2.0).
- `parser/text_blocks.py`: block/line/span/word with bbox.
- `parser/table_detector.py`: baseline grouping + column-gap segmentation; conservative
  table/partial/unresolved classification and uncertainty reasons.
- `parser/table_rebuilder.py`: detected layout → domain `Table`.
- `parser/candidate_registry.py`: every cell → candidate bound to table/row/cell/page/bbox.
- `parser/pipeline.py`: PDF → artifacts → candidates → `run_manifest.json`.
- `storage/artifact_store.py` + `storage/run_store.py`: atomic JSON, per-artifact SHA-256,
  sanitized config (API key value never written).
- CLI parse/render/tables/candidates/report implemented.

### Tests

```text
python -m pytest
39 passed in 5.32s
```

Phase 1 proof (real run on synthetic fixture):

```text
tables: [('p001-t01', 'recommended_operating', ...), ('p001-t02', 'absolute_maximum', ...)]
3.3 -> doc-...:p001-t01-r01-c02 | table p001-t01 | role typ
3.3 -> doc-...:p001-t02-r01-c01 | table p001-t02 | role min
```

The same numeric text in two tables yields two distinct candidate IDs.

### Known limitations

1. Table detector uses text alignment only; vector-line/merged-cell reconstruction is partial.
2. No OCR: pages without a text layer produce zero candidates (by design, not guessed).
3. Detector heuristics (8 pt cell gap, 2.5× row gap, ±2 column tolerance) are configurable
   only in code so far; move to `configs/parser.yaml` in the next iteration.
4. Multi-page continuation tables are emitted as separate tables per page (page binding is
   correct, logical merging is not implemented).
5. CLI dependencies (`typer` / `rich` / `python-dotenv`) are installed in the current
   environment and declared in `pyproject.toml`; CI must run `pip install -e ".[dev]"`.

### Next round (Phase 2)

DashScope provider, prompt builder, candidate-only output schema, and Python-side
validation of candidate ownership + evidence alignment.

---

## Round 3 — Phase 1.1 real-datasheet diagnosis (2026-11-05)

**Status:** diagnostic only; Phase 1 **not accepted**; Phase 2 remains blocked.

- Coordinate chain fixed from empirical PyMuPDF 2.0 evidence: `get_text()` bboxes
  are unrotated user-space; `page.rect` is post-crop/post-rotate. Added
  `PageGeometry.to_display_bbox()` (0/90/180/270 + CropBox) and routed text
  blocks through it; renderer uses integer DPI required by PyMuPDF 2.0.
- Thresholds moved to `configs/parser.yaml` (`cell_gap_pt`, `row_gap_factor`,
  `column_tolerance`, `header_min_hits`, `max_title_chars`, `max_cell_chars`,
  `min_numeric_cells`); effective config + SHA-256 recorded in `run_manifest.json`.
- Real PDFs parsed: LM358 (68p), ADS1299 (84p), ADC12DJ5200 (180p).
- Critical finding: severe over-detection (412/391/891 tables; median 1 row;
  unknown table_type 410/389/889; `not_a_table` 236/199/413).
  Candidate bbox localization is 60/60 in the 20-per-model sample, but row/column
  attribution is mostly unverifiable because headers are not recognized.
- Full evidence and failure cases: `docs/PHASE1_1_DIAGNOSIS.md`,
  `docs/phase1_1/<model>/`.
- Tests: `python -m pytest -q` → 48 passed.
- Decision: do not enter Phase 2; first fix Table Detector boundaries/headers
  and build a human-labelled table gold set.



---

## Round 4 — Phase 1.2 Gold Set and five-layer detector (2026-11-05)

**Status:** first refactor round complete; reviewer approval requested. Phase 2 frozen.

- Frozen baseline: commit `1d8c7220601db734b63437abd41c36739a42aa89`, tag
  `phase1.1-baseline`. All comparisons use `gold/gold_table_set.jsonl`
  (annotation `gold-2026-11-05.1`, 45 tables + 19 negatives).
- New layers, each in its own module:
  `parser/layout.py` (page layout) -> `parser/table_regions.py` (region
  detection) -> `parser/structure.py` (structure) ->
  `parser/header_semantics.py` (header/roles/type) ->
  `parser/candidate_registry.py` (candidate binding).
  `parser/table_detector.py` is orchestration only.
- Config additions (`configs/parser.yaml` -> `TableParams`):
  `rule_min_width_pt=70.0`, `rule_min_height_pt=15.0`, `alignment_min_rows=3`.
- Behaviour: rule lattices are the only region source; text alignment is a
  fallback for pages with no vector rules and needs >= 3 visual rows. Hard
  column rules must cover >= 55% of the table height and be crossed by text in
  < 40% of bands. Soft boundaries need header labels or recurring body gutters
  and are skipped where a hard rule or header words already own the interval.
  Ragged data rows now force `partial` rather than `reconstructed`.
- Gold set tooling: `tools/goldset/rules.py`, `annotate.py`, `inspect_components.py`,
  `evaluate.py`, `compare.py`; visual overlays in `gold/overlays/`, gallery
  `gold/review.html`.
- Results on the same Gold Set (`gold/comparison.md`):
  P 0.0492 -> 0.9070, R 0.3556 -> 0.8667, F1 0.0865 -> 0.8864;
  FP 309 -> 4; negative FP 59 -> 4; out-of-scope 68 -> 7.
  Row exact 5/16 -> 38/39; column exact 12/16 -> 34/39;
  header column accuracy 0.0413 -> 0.5932; role accuracy 0.0331 -> 0.6398;
  table-type accuracy 0 -> 0.5128. Mean overlapping predictions 5.911 -> 0.867.
- Physical chain unchanged: 60/60 sampled non-empty candidates still cover ink.
- Tests: `python -m pytest -q` -> 48 passed.
- Remaining failures and known trade-offs are listed in
  `docs/PHASE1_2_ARCHITECTURE.md` (6 FN, 4 negative FP, six structure
  mismatches, including the intentionally dropped partial sub-rule in
  `LM358-P04-T01`).
- No LLM, no DashScope, no automatic parameter generation in this round.

---

## Round 5 — Phase 1.2 round 2: gold review + header/role semantics (2026-11-06)

**Status:** second refactor round complete; reviewer approval requested. Phase 2 frozen.

- Gold annotation `gold-2026-11-06.1`: 46 tables + 19 negatives. Independent
  review complete for 65/65 items (`gold/independent_review.json`,
  `gold/review_record.md`, `manifest.json` `items_pending: 0`). Corrections:
  `ADC12DJ5200-P01-T01` added (missing p.1 package table);
  `ADC12DJ5200-N01-P01-FEATURES` bbox narrowed so it no longer covers that table.
  Open gold ambiguities are documented and deliberately frozen.
- Header semantics (`parser/header_semantics.py`): header depth from vertical
  merges, ordinal headers, sparse lead rows and third-row pin counts; canopy
  propagation no longer overwrites the leading row-header column; ordinal groups
  spread evenly; whitespace-free header comparison in the evaluator with an
  exact-spacing strict variant.
- Column roles: limit words only count in short labels (`MAXIMUM SAMPLING RATE`
  is VALUE); selectors (`MODE`, `CLOCK SOURCE`, `REFERENCE CLAUSE`, package
  options) are CONDITION; `acronym` is SYMBOL and `Register Name` is VALUE;
  leading column defaults to SYMBOL except part/address/bit/sample-code or a
  stimulus with a unit; unlabeled columns left of MIN/TYP/MAX are CONDITION.
- Metrics: same 46-table set on both sides (baseline re-evaluated through the
  evaluator). Detection TP/FP/FN 16/309/30 -> 46/0/0; negative FP 59 -> 0;
  out-of-scope 68 -> 8. Structure: row exact 5/16 -> 46/46; column exact
  12/16 -> 44/46; header column accuracy (compact) 1.0000 on 287 columns (44
  tables), strict 0.9582; header depth 46/46; multi-layer 10/10; header
  cell-text F1 1.0000; role accuracy 0.9897 (292 columns), role exact 41 tables;
  table-type 0.5870; cell-text F1 0.8889.
- Residual mismatches: 2 column splits (gold ambiguity), 3 role columns
  (`ADS1299-P27-T01`, `ADC12DJ5200-P46-T01`, `LM358-P04-T02`), 12 strict-spacing
  header columns (`fCLK`, `µV`). Header/role denominators are printed in
  `gold/comparison.md`; confusion matrices and error cases in
  `gold/after_report.md`.
- Tests: `python -m pytest -q` -> 48 passed.
- Candidate Registry unchanged; no LLM, no DashScope, no automatic parameter
  generation. Not pushed to Codeup this round.

---

## Round 6 — Phase 1.3 evidence-chain slice (2026-11-06)

**Status:** first Phase 1.3 slice complete; Phase 2 still frozen.

- Evidence model: `Table.header_cells` records the printed header cell behind
  every column/level label (id, level, column, bbox, page, source cell);
  `Candidate.role_source` (`header_text` / `heuristic` / `fail_closed`) and
  `Candidate.role_header_cell_id` record where a role came from.  All fields are
  optional and did not change parser decisions.
- New validator `tools/validate_evidence.py` resolves every candidate to
  table/row/cell, checks box containment, page bounds, header path/refs, role
  provenance, and manifest counts.  `--strict` fails on warnings.  Negative
  tests cover missing/cross-table references, bbox mismatches and out-of-page
  boxes, broken header paths, missing header cells and role conflicts.
- Re-parsed the three reference PDFs into `runs/phase13_evidence` (ignored):
  LM358 39 tables / 5,631 candidates / 272 header cells; ADS1299 56 / 2,651 /
  354; ADC12DJ5200 301 / 9,328 / 1,609.  Validator: 0 errors, 0 warnings on all
  three runs.
- Regression: same gold evaluation gives TP/FP/FN 46/0/0, row exact 46/46,
  column exact 44/46, header compact 1.0000, strict 0.9582, depth 46/46, role
  0.9897.  No metric changed.
- Gold version policy: `docs/GOLD_SPEC.md` defines `visual_boundary` vs
  `logical_column`, partial condition bands, merged cells, unlabeled columns
  and bit-field negatives.  `tools/goldset/freeze_version.py` snapshots
  `spec.yaml` + derived files into `gold/versions/<annotation_version>/` and
  refuses to overwrite.  `gold-2026-11-06.1` is frozen at source commit
  `b8c2d3b`.
- Tests: `python -m pytest -q` -> 63 passed.
- Known gaps: cross-page continuation metadata is not yet in the run contract;
  gold v2 is documented but not migrated; no untuned vendor PDF has been
  annotated yet.  See `docs/PHASE1_3_EVIDENCE.md`.
- Not pushed to Codeup; no LLM, DashScope or automatic parameter generation.

---

## Round 7 — Phase 1.3 cross-PDF generalization (2026-11-06)

**Status:** generalization slice complete; Phase 2 still frozen.

- Freeze first: `gold/generalization/PARAMS_FROZEN.json` records parser commit
  `f8032cc` (tag `phase1.3-evidence-slice1`), `configs/parser.yaml` SHA-256 and
  the three document SHA-256 values, committed in `f77ccb1` before any run.
  No parser parameter changed afterwards.
- New documents (never used for tuning): Micrel MICRF103 (7p), TI DS10CP152
  (17p), TI CY29FCT520T (12p).  Runs `runs/phase13_generalization/` are ignored:
  6 / 13 / 14 tables, 1,201 candidates.  `validate_evidence --strict`: 0 errors,
  0 warnings on all three.
- Gold `gen-2026-11-06.1`: 19 tables + 8 negatives, built from the independent
  rule lattice with explicit `column_boundaries`, `row_boundaries`, `bbox` and
  header `merges`; every overlay checked.  Tooling gained multi-component merge
  (`component: [...]`), bbox/row overrides and `--spec/--out-dir` so new gold
  lives beside the Phase 1.2 set instead of overwriting it.
- Results on the frozen parser: TP 18 / FP 9 / FN 1, P 0.6667, R 0.9474,
  F1 0.7826; 6 negative FPs; 6 out-of-scope predictions.  Per PDF: MICRF
  2/4/1, DS10 11/1/0, CY29 5/4/0.  Rows 18/18, columns 15/18, cell F1 0.8637,
  header 92/92 compact and strict, depth 17/18, header-cell F1 0.9892,
  multi-layer 4/4, role 0.8542, table type 0.6111.
- Error families: rule-poor table boundary (MICRF103 p3), drawings as false
  positives (pinout, pipeline, package, schematic, header band), sub-rules
  promoted to columns, one invented header on a headerless list, and `unknown`
  leading columns guessed as `symbol`.
- `unknown` is no longer coerced to `value` by the evaluator; Phase 1.2 metrics
  are unchanged (46/46, 0 FP, 46 rows, 44 columns, header 1.0000/0.9582, role
  0.9897 against frozen gold `gold-2026-11-06.1`).
- Evaluator fix: `--out` / `--json` / `--csv` no longer default to
  `gold/baseline_*`.  Previously every ad-hoc run rewrote the frozen baseline
  tables CSV; now outputs are written only when a path is passed.
- Docs: `docs/PHASE1_3_GENERALIZATION.md`; `docs/GOLD_SPEC.md` now names
  schematic/drawing/layout negatives; `gold/README.md` documents the
  generalization set and the frozen-parameter rule.
- Not pushed to Codeup; no LLM, DashScope or automatic parameter generation.

---

## Round 8 — Gold Spec v2 + independent gold review (2026-11-06)

**Status:** gold-side work complete; generalization metrics are internal only;
Detector code untouched.

- **Gold Spec v2.** `docs/GOLD_SPEC.md` resolves the v1 contradiction by
  recording `visual_columns` + `visual_boundary_status` separately from
  `logical_columns`, with four metrics that have distinct denominators and
  exclusions (visual boundary, logical column, header attribution, role
  accuracy).  `merged_cells` is span-based and points at cells; `no_merge`
  points at boundary segments.  Ambiguous tables are no longer excluded
  wholesale; only the specific metric with no comparable representation is.
- **Tooling.** `tools/goldset/annotate.py` accepts `merged_cells` /
  `no_merge` / `visual_columns` / `logical_columns` / `partial_boundaries`,
  supports `component: null` (synthetic component built from `page_segments`
  plus axis-aligned quadrilateral cell outlines), and derives the review-record
  path from `--out-dir`.  `tools/goldset/evaluate.py` emits the four new
  column metrics plus mismatch cases.  `tools/goldset/rules.py` de-duplicates
  identical overprinted word objects (CY29 UNIT overprint).
  New `tools/goldset/render_review_crops.py` renders standalone PDF crops for
  independent review.
- **Independent review.** `gold/generalization/independent_review.json` and
  `review_record.md`: all 21 tables and 8 negatives checked PDF-first on
  overlay-free crops.  Statuses: 9 confirmed, 9 confirmed_with_note,
  11 corrected.  Corrections: added CY29FCT520-P10-T01 and
  DS10CP152-P13-T02, shrank DS10CP152-N03-P13 to the drawing, reclassified
  DS10CP152-N01 as prose, re-drew all negatives.  Provenance defect recorded:
  five of eight v1 negatives were parser boxes and three were rule components.
- **Gold `gen-2026-11-06.2`:** 21 tables / 8 negatives (MICRF 3/2, DS10 12/3,
  CY29 6/3).  `gen-2026-11-06.1` remains frozen and immutable.
- **Internal results on the frozen parser:** TP 19 / FP 7 / FN 2, P 0.7308,
  R 0.9048, F1 0.8085; 4 negative FPs; 7 out-of-scope.  Rows 19/19, visual
  boundary 11/17, logical column 16/19, cell F1 0.8443, header 95/95, depth
  18/19, header-cell F1 0.9896, multi-layer 4/4, role 0.8586, type 0.6316.
  New FN families: MICRF103-P03 fragmentation (outer boundary) and
  DS10CP152-P13-T02 (quadrilateral-only ruling, invisible to line/rect
  detection).
- **Not an acceptance version.** Phase 2 stays frozen, the generalization gate
  stays open, and no unreviewed metric is packaged as a pass.  Detector
  parameters are frozen; no MICRF-specific special case was written.
- Not pushed to Codeup.

## Phase 1.4 S1 — RulePrimitive / RuleComponent / TableRegion

**Status:** S1 implemented and locally committed; awaiting Reviewer.  Phase 2
and S2/S3/S4 remain frozen.

- **Files.** New `src/icpdf/parser/rule_primitives.py`.  Rewritten
  `table_regions.py` (component aggregation).  `layout.py` re-exports the new
  model.  `structure.py` gains `RegionEvidence` and region fields.
  `header_semantics.py` accepts headerless ruled label grids.
  `table_detector.py` / `table_rebuilder.py` / `domain/table.py` carry
  `region_components`, `boundary_source`, `merge_evidence`.
  `config.py` only adds merge-threshold defaults; the YAML config SHA stays
  `ab9f1252…`.
- **Behaviour.** `line` + `thin_rect` + stroked `qu` edges are primitives with
  drawing provenance.  Components are connected physical lattices.  Regions
  merge stacked components with shared lattice (gap 2–24pt, extent within 3pt,
  no larger-than-body caption in the gap) and imply outer boundaries from
  common horizontal-rule extents.  Absorbed components are not emitted twice.
  A headerless fully ruled key/description grid is accepted as a table.
- **Tests.** `tests/unit/test_rule_primitives.py`,
  `tests/unit/test_table_regions.py`, `tests/integration/test_phase14_s1.py`;
  full suite `78 passed, 2 xfailed` (CY29 block diagram / package drawing are
  S3 xfails).
- **Runs (git-ignored).** `runs/phase14_s1/final_phase12/` (3 PDFs),
  `runs/phase14_s1/final_generalization/` (3 PDFs); all six pass
  `tools.validate_evidence --strict` with 0 errors.
- **Gold v2.** TP 21 / FP 4 / FN 0, P 0.8400, R 1.0000, F1 0.9130 (was
  19/7/2).  MICRF103-P03-T01 now IoU 1.0 (30×6, implied outer); DS10CP152-P13-T02
  now IoU 0.9812 (5×2).  Negative FPs unchanged at 4.
- **Phase 1.2.** TP 46 / FP 0 / FN 0 unchanged item-by-item; 8 out-of-scope
  predictions unchanged; 0 negative FP.  Two unannotated pages (LM358 P42,
  ADS1299 P78) now expose the same tape-dimension table; no metric impact.
- **Docs/evidence.** `docs/PHASE1_4_S1.md`;
  `docs/evidence/phase14_s1/{micrf103_p03,ds10cp152_p13}_detected.png` rendered
  by the new `tools/render_detection_crops.py`.
- **Left over.** S3 drawing gate (4 negative FPs), S2 visual/logical columns
  and `condition_path`, S4 roles, fill-only quad outlines, cross-page regions.
- Not pushed to Codeup.

### S1 review follow-up (2026-11-06)

- **S1 commit:** `003311fa8ee24ef68254fa3852329a9a9f1d762a`; follow-up changes
  are a separate local commit.
- **Files.** `table_regions.py` caption block now matches caption text
  (`Table`/`Tabelle`/`Tabla`/`表`/`Figure`/…), not font size;
  `config.py` drops `merge_caption_scale` (YAML/config SHA unchanged);
  `header_semantics.py` `_is_label_grid` also requires a description cell
  (≥3 words/≥15 chars) beside the short key.
- **Tests.** `tests/unit/test_table_regions.py` adds larger-heading merge,
  body-size caption split, independent-tables split, section-local column
  mapping; new `tests/unit/test_label_grid.py` (7 negative/positive cases).
  Full suite `89 passed, 2 xfailed`.
- **Reruns.** `runs/phase14_s1/review_rerun/` six runs, evidence 0/0;
  Gold v2 and Phase 1.2 per-item diffs are empty (`changed_items=[]`).
- **Review artifacts.** `docs/reviews/phase14_s1/` (response, components/grid
  JSON + images, per-item diff JSON, commit patches).

## Phase 1.4 S2 — design and data-model proposal (2026-11-06)

**Status:** design only, submitted for Reviewer confirmation; **no S2 code has
been written**.  S1 behaviour, Gold v2 (`gen-2026-11-06.2`), the config SHA and
Phase 2 stay frozen.

- **Docs.** New `docs/PHASE1_4_S2.md` (scope, measured current state, visual
  and logical boundary rules, projection, section/condition bands, fail-closed
  behaviour, additive data model, evaluation split, validator checks, tests,
  slices, 12 open questions).  `docs/PHASE1_4_STRUCTURE_MODEL.md` status line
  points to it; its old `logical_columns <= visual_columns` invariant is
  withdrawn because Gold v2 contradicts it (CY29 P04-T01 8 logical / 4 visual).
- **Measured basis (frozen S1 probe).** Full-height separator coverage is
  0.871–1.000, body sub-rules 0.072–0.576; a 0.85 threshold separates them.
  CY29 P05 `193.9`/`266.0` (0.556) demote; CY29 P06 `290.2` (0.576) promotes
  on repeated short labels `Data`/`I`; DS10 P04 `346.1` (0.108) and P05
  `363.1` (0.422) demote.  MICRF P03 section rows 1/9/15/19 are bold solo rows
  with no crossing rules (gold span 6); DS10 section rows are crossed by
  internal verticals (gold span 2).
- **Proposed code (after approval only).** New `src/icpdf/domain/logical.py`
  (shared models, parser-level `PhysicalCellRef` / `LogicalHeaderRef`) and
  `src/icpdf/parser/logical_structure.py` (builder); `table_rebuilder`
  resolves refs to existing domain cell/row ids without changing the S1 id
  scheme.  Additive fields on `TextSpan`, `DetectedTable`/`DetectedCell`/
  `DetectedRow`, domain `Table`/`Cell`/`TableRow`, `Candidate`
  (+`CandidateType.SECTION`); additive `TableParams` defaults only (YAML
  unchanged).  No change to `rule_primitives.py`, `table_regions.py`,
  `structure.py` behaviour or `grid.xs`.
- **Proposed evaluation.** Separate `pred_visual_columns` and
  `pred_logical_columns`; visual denominator 19, logical denominator 21;
  legacy physical `pred_columns` reported separately and required to be
  item-by-item identical to S1 on the 46 + 21 frozen tables.
- **Design-time expectation (not an acceptance claim).** Visual 19/19,
  logical 20/21; CY29 P08 `not_printed` is a known 9-vs-12 undercount and is
  reported as a miss, not forced.
- **Awaiting.** Reviewer answers to the 12 open questions (section evidence,
  invariant correction, section span rule, promoted-subcolumn role, fail-closed
  granularity, thresholds, P08 deferral, status handling, field migration,
  `SECTION` candidates, `TextSpan.flags`, `partial_condition_band` shape).
- Not pushed to Codeup.

## Phase 1.4 S2 — design revision r1 (2026-11-06)

**Status:** design-only revision submitted for confirmation; **still no S2
code**.  Reviewer approved the architecture, three-lattice split, visual/logical
metric split and table-level fail-closed, but withheld S2a pending three P0
data-model fixes and the `ConditionContext` clarification.

- **P0-1 many-to-many cells.** Physical cells no longer carry a single
  `logical_cell_id` / `logical_column`.  `LogicalCell.physical_cell_refs` is the
  authoritative reverse map; physical cells get derived multi-valued
  `logical_cell_ids` / `logical_columns`; word ownership is a partition.
  Candidates keep physical identity (`candidate_id = document:cell_id`) and
  gain `logical_cell_refs` / `logical_columns`; conflicting multi-role mappings
  fall back to `unknown` + `multi_logical_mapping`.  Synthetic straddling-cell
  case added to the test plan.
- **P0-2 header provenance.** `LogicalHeaderRef` now carries
  `logical_header_id`, `source_header_cell_refs`, `source_cell_refs` and
  `evidence_word_ids`, resolved in `table_rebuilder` to domain id lists.  A
  logical header with text but no source evidence is a validator error.
- **P0-3 row contract.** All `row_start` / `row_end` / `source_row` use the
  zero-based physical grid row, inclusive at both ends; array position would be
  a separate `row_index` and is out of scope.  Validator form:
  `0 <= row_start <= row_end <= n_rows - 1`.
- **ConditionContext.** `ConditionBand` stays a physical evidence region;
  candidate inheritance moves to a separate `ConditionContext`
  (`condition_band_id`, `target_candidate_ids`, `association_evidence` =
  `row_overlap` / `header_path` / `column_map` / `explicit_subrule_label`).
  Same-row membership alone is not evidence.
- **Reviewer decisions.** All 12 r0 questions answered (§14); thresholds
  (0.85 coverage, 2 words, 12 chars, 0.5 ratio, 0.90 bold, 4pt span, 0.5pt
  crossing epsilon) are experimental and must live in `TableParams` with a run
  parameter-snapshot hash.  `unresolved_section_hint` added for section-like
  rows lacking bold evidence; SECTION candidates are context-only
  (`eligible_for_parameter_extraction = false`); `partial_condition_band` is
  not implemented.
- **New sections.** §14 recorded decisions, §16 frozen acceptance red lines,
  §7.0 row contract, §7.4 ConditionContext, §12 synthetic P0-1 / context /
  provenance tests, S2-design-r1 slice row.
- Still not pushed to Codeup; no PDF rerun and no Gold change.

## Phase 1.4 S2a — VisualBoundary implementation (2026-11-06)

**Status:** S2a implemented, six-PDF rerun and evidence bundle ready for
independent review; **not self-declared passed**; S2b/S2c not started; not
pushed to Codeup.

- **Code.** New `src/icpdf/domain/visual.py` (frozen `VisualBoundary` + role
  vocabularies) and `src/icpdf/parser/visual_structure.py`
  (`build_visual_structure`).  `TableParams` gains
  `visual_min_rule_span_pt`, `visual_boundary_tol_pt`,
  `visual_full_height_coverage`; `pipeline` writes `table_params` and
  `table_params_sha256` into `run_config.json` and `run_manifest.json`.
  `DetectedTable`/`Table` carry `visual_boundaries`,
  `visual_boundary_status`, `visual_columns`, `partial_boundaries`,
  `visual_boundary_evidence`; `table_rebuilder` copies them.  `grid.xs/ys`,
  physical cell bbox/text and Candidate IDs unchanged.
- **Algorithm.** Vertical ruling ≥4pt within 2.5pt of the region x-range;
  collinear grouping; clipped-union coverage over region height; outer edges
  always present; partial when coverage < 0.85; status precedence
  `not_printed` → `partial` → `implied_outer` (single-sided outer per
  Reviewer rule) → `printed`; `visual_columns = internal + 1`, `null` only
  for `not_printed`.
- **Effective parameters.** `table_params_sha256 =
  82d4df4d1cb3cac9741831b0db36e19fa80c1829abc18b3f8b1ab4ee1c6b9f0a`;
  parser YAML config SHA unchanged
  (`ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c`).
- **Evaluator.** Visual predictions from `visual_columns`; legacy physical
  fallback for pre-S2a runs; visual column denominator excludes gold
  `not_printed`; logical metric unchanged (S2b not authorized).  CSV/Markdown
  expose `pred_visual_columns` / `pred_visual_status` / partial boundaries.
- **Validator.** 26 `VISUAL_*` codes plus `PARAM_SNAPSHOT_HASH` and
  `CONFIG_PARAMS_MISMATCH`; thresholds read from the manifest snapshot.
  One negative test per visual code.
- **Results.** 127 passed, 2 xfailed.  All six S2a runs: `errors=0
  warnings=0 --strict`.  Gold v2: visual columns 19/19 exact, `not_printed`
  predicted null 2/2, visual status 18/19, logical 18/21 identical to S1,
  rows 21/21.  Phase 1.2: TP 46 FP 0 FN 0; all non-visual metrics identical
  to the S1 control.  `runs/phase14_s2a/physical_diff.json`: 430 tables /
  18,899 candidates, 0 diffs; `gold_item_diff.json`: 67/67 gold items, 0
  field diffs.
- **Known divergence.** DS10CP152-P03-T01: gold `partial` [331.0], predicted
  `printed` at coverage 0.952 (threshold 0.85); visual columns 2/2 agree.  No
  threshold separates it from MICRF103 P03 (0.881, must stay `implied_outer`);
  reported rather than tuned.  Phase 1.2 gold has no visual annotations, so
  its visual metric is diagnostic only (legacy fallback), not acceptance.
- **Artifacts.** `docs/PHASE1_4_S2A.md`;
  `runs/phase14_s2a/{generalization_report,phase12_report,s1_*_control,
  physical_diff,gold_item_diff}.{json,md,csv}` (runs/ is gitignored).
- **Implementation commit.** `e6cba6bac51d8e3f5d4091b98ded46409042276e`
  (`feat(parser): Phase 1.4 S2a visual boundary lattice`), local only.

## Phase 1.4 S2a — Reviewer round r1 (2026-11-06)

**Status:** review feedback addressed; code, tests, validator results and the
updated S2a report are ready for final review.  Not self-declared passed;
S2b/S2c not started; not pushed to Codeup; Gold v1/v2, S1 physical rules and
thresholds untouched.

- **P1 status precedence.** Frozen rule (doc §3.1): no internal → `not_printed`;
  any internal below full → `partial`; all internals full + both outers drawn →
  `printed`; all internals full + ≥1 outer implied → `implied_outer`.  An outer
  deficit alone never yields `partial`.  Six synthetic combination tests.
- **P2 provenance.** `VisualSegment(component_id, y0, y1, primitive_indices)`
  added to `VisualBoundary.segments`; implied outers carry no segment,
  `component_ids=[]`, `coverage=0`.  `primitive_indices` index the page-level
  `collect_primitives()` list.  Real sample:
  `runs/phase14_s2a/review_r1/visual_evidence_sample.json`.
- **P3 determinism.** Segments sorted by `(c, a, b, component_id)` and grouped
  against a fixed anchor, group x = mean computed after close; running-mean
  chain drift removed.  Two tests (order independence, 100.0/102.4/104.4/106.4
  → two groups).
- **Validator independence.** New `_validate_visual_segments` recomputes
  coverage from recorded clipped spans (1e-6), checks segment count,
  `component_ids`, segment spans, primitive index shape, and outer `drawn`
  against recomputed coverage.  New codes: `VISUAL_SEGMENTS_MISSING`,
  `VISUAL_SEGMENT_COUNT`, `VISUAL_COMPONENT_IDS_MISMATCH`,
  `VISUAL_SEGMENT_COMPONENT`, `VISUAL_SEGMENT_SPAN`, `VISUAL_SEGMENT_PRIMITIVE`,
  `VISUAL_COVERAGE_RECOMPUTE`, `VISUAL_DRAWN_BELOW_FULL`,
  `VISUAL_IMPLIED_ABOVE_FULL`.
- **Tests.** `146 passed, 2 xfailed`; `test_visual_structure.py` 21,
  `test_phase14_s2.py` 11, `test_evidence_validation.py` 40.
- **Runs.** Six fresh review-r1 runs under
  `runs/phase14_s2a/review_r1/`; manifests and counts in doc §7.  First-pass
  runs superseded (no segment evidence).
- **Results.** All six runs: validator 0 errors / 0 warnings (`--strict`).
  Gold v2: visual columns 19/19, `not_printed` null 2/2, visual status 18/19,
  logical 18/21, rows 21/21.  Phase 1.2: TP 46 / FP 0 / FN 0.  Physical diff:
  430 tables / 18,899 candidates / 0 diffs; gold items 67/67 / 0 diffs.
  Visual fields across 430 tables identical to the first pass (0 diffs).
- **Known divergence.** DS10CP152-P03-T01 `partial` vs `printed` kept and
  documented; no threshold tuning.
- **Implementation commit.** `f48ecd5c3e822ecb20af03f304a252ef09cd27c8`
  (`fix(parser): address S2a review r1 provenance and status precedence`),
  local only, not pushed.

## Phase 1.4 S2a — Reviewer round r2 primitive audit (2026-11-06)

**Status:** provenance authenticity audited; ready for final review.  No parser,
visual-algorithm, validator, Gold or threshold change; S2b/S2c not started;
not pushed to Codeup.

- **New read-only tool.** `tools/audit_visual_primitives.py` re-opens the
  source PDF, re-runs `collect_primitives(page, page_number, geometry)`,
  resolves every `primitive_indices` entry, checks component ownership,
  vertical orientation, x within 2.5pt, primitive span inside the segment span,
  rebuilds segment envelopes and recomputes coverage from raw primitives.
  Reports `PRIMITIVE_INDEX_OUT_OF_RANGE`, `PRIMITIVE_NOT_VERTICAL`,
  `PRIMITIVE_X_MISMATCH`, `PRIMITIVE_NOT_IN_COMPONENT`,
  `PRIMITIVE_OUTSIDE_SEGMENT`, `SEGMENT_SPAN_MISMATCH`, `COVERAGE_MISMATCH`,
  `DRAWN_WITHOUT_SEGMENTS`, etc.  CLI audits a frozen run's `tables.json` with
  `--run/--gold/--item-id/--out`; exit 1 on issues.
- **Index space.** `primitive_indices` are positions in the page-level
  `collect_primitives` list, explicitly not `drawing_index` (DS10 p4: 79/442
  differ; MICRF p3: 23/58; CY29 p5: 333/334).  Docstrings in `domain/visual.py`
  and `visual_structure.py` state this.
- **New tests.** `tests/integration/test_phase14_primitive_audit.py` (7):
  DS10CP152 P04 internal partial, MICRF103 P03 implied outer (no primitive
  backing), CY29FCT520 P05 multiple partials, index-space proof, tampered
  out-of-range index, horizontal primitive, stretched/shifted segment span,
  faked drawn outer with no segments.  PDFs absent → skip.
- **Audit results.** Persisted review-r1 evidence, 0 issues each:
  DS10CP152-P04-T01 (9 boundaries; x=346.15 coverage 0.108187 from primitives
  278+295), MICRF103-P03-T01 (7 boundaries; implied outers 0 segments /
  0 primitives), CY29FCT520-P05-T01 (8 boundaries; partials 193.946/265.958
  coverage 0.555596).  Artifacts:
  `runs/phase14_s2a/review_r2/audit_{ds10_p04,micrf103_p03,cy29_p05}.json`.
- **Tests.** `153 passed, 2 xfailed`; prior six-run validator results and all
  Gold/physical-diff evidence unchanged (validator source untouched).
- **Implementation commit.** `4246c41d208467a3e0d5537f6fbcb2675c9a13bb`
  (`test(parser): audit S2a visual evidence against raw PDF primitives`),
  local only, not pushed.

## Phase 1.4 S2a — Reviewer round r2 identity/rebuild hardening (2026-11-06)

**Status:** r2 audit now fails closed on identity and proves the component
rebuild; parser, visual algorithm, validator, Gold and thresholds untouched;
S2b/S2c not started; not pushed to Codeup.

- **Identity gate (P1/P4).** `verify_identity()` checks artifact SHA-256
  (`document.json`, `pages/geometry.json`, `tables.json`, `run_config.json`),
  `source.pdf` SHA-256 against both the manifest and `document.json`,
  page count / DPI agreement, fresh `load_pdf(dpi=manifest)` page sizes,
  rotations, CropBox, MediaBox and display rect, and the table-parameter
  snapshot hash recomputed with `snapshot_sha256()`.  `AuditIdentityError`
  refuses the run (CLI exit 2); a same-product wrong-version PDF is rejected.
- **Snapshot binding (P4).** Audit thresholds are read from
  `manifest.table_params`; no visual-threshold literal is used.
- **Component rebuild (P2).** The audit re-runs
  `collect_primitives()` → `build_components()` and only accepts the fresh
  component set; it checks bbox containment, a vertical ruling at x, and
  primitive ownership, and reports the rebuilt counts in a `rebuild` block.
- **Strict segment rebuild (P3).** Stored `y0`/`y1` must equal the min/max of
  clipped raw primitive spans; coverage comes from the union of raw primitive
  spans; duplicate and cross-component primitive references are rejected.
- **New tests.** `tests/integration/test_phase14_primitive_audit.py` now has 11
  tests, adding spec/manifest identity, wrong-version refusal, duplicate
  primitive and cross-component negatives.
- **Results.** `157 passed, 2 xfailed`; six review-r1 runs still pass the strict
  validator with 0 errors / 0 warnings; three audit artifacts regenerated with
  0 issues.  Artifacts:
  `runs/phase14_s2a/review_r2/audit_{ds10_p04,micrf103_p03,cy29_p05}.json`.
- **Implementation commit.** `ff38d2e` (`fix(parser): harden S2a primitive
  audit identity and rebuild checks`), local only, not pushed.

## Phase 1.4 S2a — Reviewer r2 re-review: GRID_TOL and artifact completeness (2026-11-06)

**Status:** the two remaining r2 questions are closed; no parser, validator,
Gold, S1 rule or threshold change; S2b/S2c not started; not pushed.

- **GRID_TOL binding (r2-P4-1).** `GRID_TOL = 2.5` lives in
  `src/icpdf/parser/rule_primitives.py` and is **not** a `TableParams` field,
  so `table_params_sha256` does not cover it.  The audit imports the same S1
  symbol, passes `tol=GRID_TOL` to `build_components`, and records in
  `identity.grid_tol`: symbol, value, source file, source SHA-256,
  `build_components`/`rule_components` defaults, `s1_defaults_match`,
  `in_table_params=false`, `covered_by_table_params_sha256=false`.  If either
  S1 default drifts from the constant, the audit refuses.
- **Required artifacts (r2-P4-2).** `REQUIRED_ARTIFACTS` is checked against the
  manifest `artifacts` list before hashing; any missing required entry is an
  `AuditIdentityError`, never a skipped file.  New
  `test_manifest_missing_required_artifact_is_refused`.
- **Tests.** `158 passed, 2 xfailed`.
- **Artifacts.** Three `runs/phase14_s2a/review_r2/audit_*.json` regenerated
  with the `identity.grid_tol` block; all 0 issues.
- **Implementation commit.** `d02e690` (`fix(parser): bind S2a audit to S1
  component tolerance and required artifacts`), local only, not pushed.
