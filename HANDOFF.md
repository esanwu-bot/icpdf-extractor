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


