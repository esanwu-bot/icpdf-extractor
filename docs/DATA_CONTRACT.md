# Data Contract (Phase 0)

**Contract version:** `data-contract/v0.2`
**Scope:** Phase 0 domain models plus Phase 1 parser output (coordinate freeze,
optional table IDs on prose evidence, explicit candidate provenance).

---

## 0. Non-negotiable principles

1. A formal parameter must be resolvable to a cell in the source PDF.
2. A number found in a PDF is not automatically a parameter.
3. A parameter match does not prove product identity.
4. Insufficient evidence goes to `unresolved` / `quarantined`, never to the formal container.
5. The requested MPN and the PDF-observed MPN are stored separately.
6. Confidence scores are hints; they never replace evidence checks.
7. Evidence is bound to a document by SHA-256, not by filename.
8. No LLM may invent a value or a `candidate_id`.

---

## 1. Coordinate system (frozen)

All `bbox` values are `(x0, y0, x1, y1)` in **PDF page display space**:

- origin: top-left of `page.rect` (`x` right, `y` down);
- unit: PDF point (`1/72 inch`);
- `x1 >= x0`, `y1 >= y0` (enforced by the model);
- space is **post-crop and post-rotation**: it is exactly PyMuPDF's `page.rect`.

PyMuPDF semantics this contract relies on:

| Object | Meaning | Contract use |
|---|---|---|
| `page.mediabox` | unrotated PDF user space media box | provenance only |
| `page.cropbox` | unrotated crop box (visible area) | provenance only |
| `page.rect` | effective rectangle after `/Rotate` + crop, origin `(0,0)` | **canonical bbox space** |
| `page.rotation` | `/Rotate` value (0/90/180/270) | recorded on `Document.page_rotations` |

Rules:

1. Every parser output bbox is normalized into `page.rect`. If an extractor
   returns unrotated coordinates, apply the page rotation matrix first and then
   re-base into `page.rect`; never mix the two spaces in one artifact.
2. For 90/270 rotation, width and height are swapped by `page.rect`; the parser
   must not "fix" them back.
3. If `page.rect` has a non-zero origin (crop offset), subtract
   `(rect.x0, rect.y0)` before reporting.
4. A bbox is only meaningful together with `page_number` and `document_sha256`.

### 1.1 Page → PNG mapping (must be stored per page)

At render DPI `dpi`, `zoom = dpi / 72.0`:

```text
pixel_x = (point_x - page.rect.x0) * zoom
pixel_y = (point_y - page.rect.y0) * zoom
pixel_w = round(page.rect.width  * zoom)
pixel_h = round(page.rect.height * zoom)
```

inverse mapping uses the same `zoom` and the stored `page.rect`. Every run stores
a `PageGeometry` record (`mediabox`, `cropbox`, `rect`, `rotation`, `dpi`, `zoom`,
`pixel_width`, `pixel_height`). A candidate bbox must round-trip through this
record back to the same PDF region within 0.5 point; a larger drift is an error,
not a rounding detail.

**Invariant I13:** `bbox_to_pixel → pixel_to_point` recovers the original bbox
within 0.5 pt for every page, including rotated pages.

---

## 2. Identity and ID rules

| Object | Identity | Uniqueness scope |
|---|---|---|
| Document | `document_id` + `sha256` | one PDF artifact |
| Product | `product_id` | one document |
| Table | `table_id` | one document |
| Row | `row_id` | one table |
| Cell | `cell_id` | one table |
| Candidate | `candidate_id` | one run |
| Evidence | `evidence_id` | one run |
| Parameter | `parameter_id` | one formal container |

Rules:

- `candidate_id` is unique inside a `CandidateSet`; duplicates are rejected.
- A `CandidateSet` may only contain candidates of its own `document_id`.
- The same numeric text in two tables produces **two** candidates with different
  `candidate_id`, `table_id`, `row_id` and `cell_id`.
- IDs are opaque strings. Formatting is a parser concern, not a semantic guarantee.

---

## 3. Objects

### 3.1 Document

| Field | Type | Invariant |
|---|---|---|
| `document_id` | non-empty str | stable within a run |
| `filename` | non-empty str | display only, never identity |
| `sha256` | 64-char lower hex | **identity anchor** |
| `page_count` | int >= 1 | must match the PDF |
| `page_sizes` | list[(w,h)] | empty or exactly `page_count` entries |
| `page_rotations` | list[int] | empty or `page_count` entries, multiples of 90 |
| `document_type` | enum | datasheet / user_guide / quick_start / errata / unknown |
| `parser_version` | non-empty str | code version that produced the artifact |
| `created_at` | aware datetime | timezone required |

The model is frozen: parsing creates a new artifact instead of mutating history.

### 3.2 Product

| Field | Invariant |
|---|---|
| `requested_mpn` | what the caller asked for, never overwritten |
| `normalized_mpn` | what the document supports |
| `identity_scope` | device / board / onboard_device / unknown |
| `identity_evidence` | required when `normalized_mpn != requested_mpn` |

`Product` never merges the two MPNs into one field.

### 3.3 Table / TableRow / Cell

`Table` records the parser's hypothesis (`table_type`); it is not a semantic
conclusion. Supported types: `absolute_maximum`, `recommended_operating`,
`electrical_characteristics`, `thermal`, `pin_functions`, `ordering_information`,
`other`, `unknown`.

Invariants:

- `page_number >= 1`; optional `page_end >= page_number`;
- every cell page is within the table's page range;
- `row_id` unique per table; `cell_id` unique per table;
- a cell's `row_id` equals its row's `row_id`; `column_id` unique within a row;
- `Cell.text` stores **raw** extracted text (never a cleaned substitute);
- `reconstruction_status = unresolved` requires `uncertainty_reason`;
- `confidence` is a parser hint only (0..1), never a correctness proof.

### 3.4 Candidate

| Field | Invariant |
|---|---|
| `document_id` / `table_id` / `row_id` / `cell_id` | all mandatory |
| `page_number` | >= 1 |
| `bbox` | ordered, `page.rect` space |
| `raw_text` | non-blank, exact source text |
| `column_role` | min / typ / max / value / condition / unit / symbol / unknown |
| `candidate_type` | parameter_name / value / unit / condition / symbol / row_label / other |
| `extraction_method` | text / vector_lines / table_detector / ocr / manual / unknown |
| `source_text_type` | **native_pdf_text / ocr / manual / unknown** |
| `reconstruction_status` | reconstructed / partial / unresolved |

`source_text_type` may never be silently upgraded: OCR-derived text stays `ocr`.
`CandidateSet` enforces: unique `candidate_id`, single `document_id`.

### 3.5 Evidence

Base fields (always required): `document_sha256`, `page_number`, `bbox`, `raw_text`.

Table/cell IDs (`table_id`, `row_id`, `cell_id`) are optional so paragraph-level
evidence can exist, but:

- `evidence_type = cell_text` → all three IDs are required;
- `evidence_type = table_row` → all three IDs are required;
- `evidence_type = paragraph` / `page_image` / `manual` → IDs may be absent.

Requirement: a reviewer must be able to re-render the same page region from
`(document_sha256, page_number, bbox)` without trusting any derived JSON.

### 3.5.1 Evidence existence is not verification

An `evidence_id` present on a parameter only proves that a reference exists.
It does **not** prove the parameter is verified. The future Audit layer must
independently check all of the following:

1. `evidence.document_sha256` equals the parameter's document;
2. `evidence.table_id` belongs to that document;
3. `evidence.row_id` belongs to that table;
4. `evidence.cell_id` belongs to that row;
5. the parameter value / min / typ / max matches `evidence.raw_text` under the
   declared normalization;
6. the unit matches the unit candidate/evidence (or is explicitly absent);
7. `applicable_mpn` matches the `Product` identity (requested vs normalized);
8. every `evidence_id` resolves exactly once; no duplicate or orphan references.

Any failed check demotes the parameter to `unresolved`/`rejected`; it must not
stay formal.

### 3.6 Parameter

| Field | Invariant |
|---|---|
| `name` | non-blank |
| `applicable_mpn` | mandatory; parameters are never global |
| `table_id` | mandatory |
| `value/min/typ/max` | at least one present |
| `evidence_ids` | non-empty for `verified` / `audited` |
| `verification_status` | verified / audited / unverified / unresolved / quarantined / rejected |
| `unresolved_reason` | required for unresolved / quarantined / rejected |

`FormalParameterSet` rejects any parameter whose status is not `verified` or
`audited`. A parameter with no evidence can never be formal.

---

## 4. State machine

```text
candidate (cell-level fact)
   │
   ├─ selected + aligned + validated ──► Parameter(verified|audited) ──► FormalParameterSet
   │
   ├─ insufficient evidence ───────────► Parameter(unresolved|quarantined)
   │
   └─ contradicted / unsafe ───────────► Parameter(rejected)
```

Rules:

- `unresolved` is a terminal state for this run; it may not be promoted without
  new evidence in a new run.
- `quarantined` keeps the raw rows for audit; it never renders as formal data.
- `rejected` means the row is known wrong (e.g. column role collapse); it must not
  be silently deleted.

---

## 5. Contract invariants (tested in Phase 0)

| ID | Invariant |
|---|---|
| I1 | A formal `Parameter` has at least one `evidence_id` |
| I2 | `unresolved/quarantined/rejected` carries `unresolved_reason` |
| I3 | `FormalParameterSet` contains only `verified/audited` |
| I4 | `candidate_id` unique inside a `CandidateSet` |
| I5 | A `CandidateSet` never mixes documents |
| I6 | Same value in two tables = two candidates |
| I7 | `bbox` is ordered and always paired with a page number |
| I8 | Evidence is anchored to `document_sha256` |
| I9 | `requested_mpn` and `normalized_mpn` are separate |
| I10 | An unresolved table carries an uncertainty reason |
| I11 | Cell text is raw, not cleaned |
| I12 | Documents are immutable (frozen models) |
| I13 | bbox → pixel → point round-trips within 0.5 pt on every page |
| I14 | cell_text / table_row evidence carries table_id + row_id + cell_id |
| I15 | Evidence presence alone never marks a parameter verified |

---

## 6. Versioning

- Any breaking field change bumps `data-contract/v0.x`.
- Artifacts record `contract_version`, `parser_version` and the SHA-256 of every
  intermediate JSON (Phase 1).
- Old runs are never rewritten; a new run gets a new `run_id`.
