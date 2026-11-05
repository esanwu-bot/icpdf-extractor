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
