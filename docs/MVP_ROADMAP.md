# MVP Roadmap

**Final principle:** prove the evidence chain before scaling extraction.

---

## Round 1 — Phase 0 (current)

Deliverables:

- project skeleton, `pyproject.toml`, configs, docs;
- Pydantic v2 models: Document, Product, Table/TableRow/Cell, Candidate/CandidateSet,
  Evidence, Parameter/FormalParameterSet;
- `DATA_CONTRACT.md`, `ARCHITECTURE.md`, `MVP_ROADMAP.md`, `DECISIONS.md`;
- unit tests, including negative tests;
- no PDF parsing and no LLM calls.

Exit gate:

- `pytest` green;
- every contract invariant I1–I12 covered by a test;
- no project code imports the old IcPdfParser.

---

## Round 2 — Phase 1 (PDF deterministic parser)

Implement:

1. PDF loader: SHA-256, page count, page sizes/rotations, encrypted/corrupt detection.
2. Page renderer: PNG at configurable DPI; record pixel/page mapping.
3. Text blocks: block/line/span/word (+characters when needed), all with bbox.
4. Table detector: vector lines + text alignment; emit uncertainty reasons.
5. Table rebuilder: rows/columns/headers/cells; `unresolved` when not provable.
6. Candidate registry: bind every candidate to table/row/cell/page/bbox; immutable artifact.

Required proof:

- synthetic PDF fixtures: simple 3-column, MIN/TYP/MAX, merged cells, multi-page,
  duplicate value in two tables, rotated text, no text layer, corrupt PDF,
  multi-MPN, incomplete table;
- a test that the same number in `recommended_operating` and
  `absolute_maximum` yields two distinct candidates;
- a test that unresolved tables never produce formal parameters.

Exit gate:

- candidate sets are accurate at row/column level on 3 real datasheets;
- page screenshots can be reproduced from `(document_sha256, page_number, bbox)`;
- interfaces frozen before LLM integration.

---

## Round 3 — Phase 2 (LLM candidate selection)

Implement:

1. Provider adapter (DashScope), model/timeout from config.
2. Prompt builder: requested MPN + identity context + table/row metadata + candidates.
3. Strict output schema; the model may only return existing `candidate_id`.
4. Python-side validation: candidate ownership, table binding, evidence alignment.
5. Integration tests with a fake provider and negative tests for invented IDs.

Exit gate:

- invented / cross-PDF / cross-table candidate references are rejected;
- unresolved output is preserved, never promoted;
- no formal parameter without evidence.

---

## Deferred (not in MVP)

Product Audit Engine, web UI, SaaS, Redis/Celery, crawler, RAG, multi-language,
SEO, alternatives, delivery packaging, goldset admin UI.
