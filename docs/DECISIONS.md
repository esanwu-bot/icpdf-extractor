# Decisions (ADR log)

## D01 — Pydantic v2 as the only domain contract

**Decision:** models are Pydantic v2 `BaseModel`, not dataclasses or ORM rows.
**Why:** one declarative place for field types and invariants; JSON round-trip
and negative tests are trivial.
**Rejected:** SQLAlchemy models in Phase 0 (would make the DB a runtime
prerequisite).

## D02 — Frozen domain objects

**Decision:** all Phase 0 models use `frozen=True`.
**Why:** a run artifact is history. Mutating it after the fact breaks replay.
**Consequence:** corrections create a new run, not an in-place edit.

## D03 — Document identity is SHA-256, not filename

**Why:** the same datasheet is downloaded under different names; filenames drift.
**Rule:** Evidence stores `document_sha256`; filenames are display-only.

## D04 — `requested_mpn` and `normalized_mpn` never merge

**Why:** a request for `AFE7950EVM` may resolve to onboard device `AFE7950`.
Overwriting either side destroys the identity audit trail.
**Rule:** if they differ, `identity_evidence` is mandatory.

## D05 — Candidate IDs are table-scoped

**Why:** the same numeric text can appear in both `recommended_operating` and
`absolute_maximum`. A global "number list" would merge two facts.
**Rule:** every candidate carries `table_id / row_id / cell_id / page / bbox`;
duplicate `candidate_id` is rejected.

## D06 — Unresolved must explain itself

**Rule:** `reconstruction_status=unresolved` requires `uncertainty_reason`;
`Parameter.status in {unresolved, quarantined, rejected}` requires
`unresolved_reason`.
**Why:** an unexplained gap is indistinguishable from a silent data loss.

## D07 — Formal parameters require evidence IDs

**Rule:** `verified` / `audited` parameters need at least one `evidence_id`;
`FormalParameterSet` rejects every other status.
**Why:** this is the line between a claim and a verifiable fact.

## D08 — Coordinate system: PDF page space

**Decision:** `(x0, y0, x1, y1)` with origin top-left and unit = PDF point.
**Open item:** Phase 1 must explicitly document rotation handling and the
page-to-pixel mapping for rendered PNGs.

## D09 — No database in Phase 0

**Decision:** SQLite may store run metadata later, but the pipeline must run
without a DB. Run artifacts are JSON files under `runs/<run_id>/`.

## D10 — Phase 0 contains no parser code

**Why:** interface freeze first; a parser written against unstable models
gets rewritten twice.
**Consequence:** `parser/`, `extraction/`, `audit/`, `storage/` are placeholders.

## D11 — bbox space is `page.rect` (post-crop, post-rotation)

**Decision:** every parser bbox uses PyMuPDF `page.rect`: origin top-left,
unit = point, after CropBox and `/Rotate`. `mediabox`/`cropbox` are provenance
only. PNG mapping is `zoom = dpi / 72`; `PageGeometry` is stored per page.
**Why:** one space, one mapping, one round-trip test (within 0.5 pt). Mixing
unrotated and rotated coordinates is the most common silent evidence bug.

## D12 — Evidence IDs are optional except for cell/table evidence

**Decision:** `Evidence` always requires `document_sha256 + page + bbox + raw_text`;
`table_id/row_id/cell_id` are required only for `cell_text` and `table_row`.
**Why:** paragraph evidence must be possible later without a fake table ID.
**Consequence:** audit must branch on `evidence_type` before checking ownership.

## D13 — Candidate provenance is explicit

**Decision:** `Candidate` records `extraction_method`, `source_text_type` and
`reconstruction_status`.
**Why:** native PDF text and OCR guesses must never be merged; a later
"normalization" step must not silently upgrade OCR to native.
**Rule:** OCR text stays `source_text_type=ocr` forever.

## D14 — Evidence presence is not verification

**Decision:** `evidence_ids` non-empty is only a reference check.
**Why:** a valid-looking ID can point to the wrong table, wrong row, wrong value
or wrong MPN.
**Consequence:** the Audit layer must verify document SHA, table/row/cell
ownership, value match, unit match and `applicable_mpn` before a parameter can
stay `verified`.

