# icpdf-extractor

**Evidence-first semiconductor datasheet extraction engine — MVP.**

Status: **Phase 1 complete** (domain contract + deterministic PDF parser + candidate registry).
No LLM extraction yet.

---

## Why this project exists

Most datasheet extractors optimise for *more rows*. This engine optimises for
*provable rows*: every formal parameter must resolve back to a cell in the
source PDF (document SHA-256 + page + bbox + raw text). Anything that cannot be
proven stays `unresolved`/`quarantined`; nothing is invented by an LLM.

Pipeline:

```text
PDF → Parser → Tables → Candidate Registry → LLM Selection
    → Evidence Alignment → Audit → Formal / Quarantine / Rejected
```

---

## Current scope (Phase 1)

Implemented:

- Pydantic v2 domain models: `Document`, `Product`, `Table/TableRow/Cell`,
  `Candidate/CandidateSet`, `Evidence`, `Parameter/FormalParameterSet`;
- frozen coordinate contract (`page.rect` display space, rotation-aware, PNG
  round-trip via `PageGeometry`);
- PDF loader (sha256, pages, encrypted/corrupt rejection);
- page renderer (PNG at configurable DPI);
- text blocks (block/line/span/word, all bbox);
- conservative table detector + rebuilder (`unresolved`/`partial` instead of guessing);
- candidate registry (table/row/cell/page/bbox bound, native-vs-OCR provenance);
- run artifacts under `runs/<run_id>/` with per-file SHA-256 and sanitized config;
- CLI: `init`, `parse`, `render`, `tables`, `candidates`, `report`; `extract` is Phase 2.

Not implemented by design:

- LLM provider, prompt building, candidate selection;
- audit engine, web UI, SaaS, queue, crawler, RAG.

## CLI

```bash
icpdf init
icpdf parse --pdf samples/example.pdf --mpn EXAMPLE123 --runs runs
icpdf render --run-id <run_id> --page 1 --runs runs
icpdf tables --run-id <run_id> --runs runs
icpdf candidates --run-id <run_id> --runs runs
icpdf report --run-id <run_id> --runs runs
```

---

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Python 3.12+ (tested on 3.13).

## Test

```bash
pytest
```

## Layout

```text
src/icpdf/
├── domain/      # frozen contracts
├── parser/      # loader / coords / renderer / text blocks / tables / candidates
├── extraction/  # Phase 2
├── audit/       # later
├── storage/     # atomic artifact + run store
└── cli.py
docs/DATA_CONTRACT.md
docs/ARCHITECTURE.md
docs/MVP_ROADMAP.md
docs/DECISIONS.md
```

## Contract highlights

- Document identity is `sha256`, never filename.
- `requested_mpn` and `normalized_mpn` are stored separately; a mismatch requires
  `identity_evidence`.
- `candidate_id` is unique per run and bound to table/row/cell/page/bbox; the
  same number in two tables stays two candidates.
- A formal parameter (`verified`/`audited`) must reference evidence; a parameter
  without evidence cannot enter `FormalParameterSet`.
- `unresolved` table/parameter must carry an explicit uncertainty reason.
- All models are frozen: corrections create a new run, not a mutation.

## Next round (Phase 2)

DashScope provider → prompt builder → candidate-only selection → Python-side
reference/evidence validation. The LLM may only return existing `candidate_id`
values; Python rejects invented IDs, cross-PDF/cross-table references and
evidence mismatches.
