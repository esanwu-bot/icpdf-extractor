# Architecture (MVP)

**Status:** Phase 0 (domain contract + skeleton). No PDF parsing implemented yet.

---

## 1. Trust boundary

```text
PDF
 │
 ▼
[PDF Parser]              deterministic, no LLM
 │  text blocks / lines / cells / tables
 ▼
[Table Rebuilder]         row/column reconstruction; unresolved allowed
 │
 ▼
[Candidate Registry]      immutable candidates bound to table/row/cell/page/bbox
 │
 ▼
[LLM Candidate Selector]  may only choose existing candidate_ids
 │
 ▼
[Evidence Alignment]      Python re-checks IDs, table ownership, bbox, raw text
 │
 ▼
[Semantic / Product Audit] independent of the LLM
 │
 ▼
Formal / Quarantine / Rejected
```

The LLM never sits on both sides of the audit. Python validates every reference.

---

## 2. Layers

| Layer | Responsibility | May depend on |
|---|---|---|
| `domain` | Pydantic models + invariants (Phase 0) | nothing else in the project |
| `parser` | PDF → text blocks / tables / candidates (Phase 1) | domain + PyMuPDF |
| `extraction` | prompt building, providers, candidate selection (Phase 2) | domain + parser artifacts |
| `audit` | independent evidence/product validation (later) | domain + artifacts |
| `storage` | run artifacts, manifests, hashes | domain |
| `cli` | thin command surface | all of the above |

Rules:

- `parser` must not import `extraction`.
- `extraction` must not write formal parameters directly.
- `audit` must not import provider modules.
- No layer may mutate a previous run directory.

---

## 3. Determinism and replay

- Every run gets a new `run_id`; old runs are immutable.
- Every artifact records its SHA-256.
- `run_manifest.json` records Python version, project version, parser version,
  model name, prompt version and candidate-set hash.
- Re-running the same PDF creates a new run and can be diffed against the old one.
- API keys are never written to artifacts or logs.

---

## 4. Phase boundaries

| Phase | Included | Explicitly excluded |
|---|---|---|
| 0 | models, contract docs, skeleton, unit tests | PDF parsing, LLM |
| 1 | loader, renderer, text blocks, table detection/rebuild, candidates | LLM extraction |
| 2 | DashScope adapter, prompt builder, candidate selection, Python reference checks | audit engine, web, SaaS |

No web UI, multi-tenancy, Redis/Celery, crawler, RAG, i18n, SEO, alternatives,
or delivery packaging in the MVP.

---

## 5. Module layout (current)

```text
src/icpdf/
├── domain/          # frozen contracts (Phase 0)
├── parser/          # Phase 1 (implemented)
│   ├── coords.py            # PageGeometry + point/pixel mapping
│   ├── pdf_loader.py        # sha256, page geometry, encrypted/corrupt rejection
│   ├── page_renderer.py     # PNG at DPI
│   ├── text_blocks.py       # block/line/span/word + bbox
│   ├── table_detector.py    # baseline grouping + column segmentation
│   ├── table_rebuilder.py   # detected layout → domain Table
│   ├── candidate_registry.py# cells → table-bound candidates
│   └── pipeline.py          # PDF → run artifacts
├── extraction/      # Phase 2 (placeholder)
├── audit/           # later (placeholder)
├── storage/         # atomic artifact + run store (implemented)
└── cli.py           # command surface
```
