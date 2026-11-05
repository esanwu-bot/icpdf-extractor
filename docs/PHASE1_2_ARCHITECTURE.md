# Phase 1.2 — Gold Set and five-layer detector

Status: first refactor round complete; awaiting reviewer approval. Phase 2 (LLM)
remains frozen.

Baseline for every number in this document: commit
`1d8c7220601db734b63437abd41c36739a42aa89` (tag `phase1.1-baseline`),
evaluated on `gold/gold_table_set.jsonl` (annotation `gold-2026-11-05.1`).
After numbers: `gold/after_report.json` (`after-5layer-v4`), same Gold Set.
Delta: `gold/comparison.md`.

## Why

Phase 1.1 detection was a single heuristic pass over text alignment. On the real
datasheets it produced 412/391/891 tables, median one row, and 236/199/413
`not_a_table`, while header and column-role recognition were effectively absent.
The reviewer verdict was "systematic over-detection; candidates are not reliable
LLM input".

This round does not tune that heuristic. It replaces it with five layers, each
with one evidence source and an explicit gate, and evaluates every change on a
frozen human-labelled set.

## Layers

| Layer | Module | Responsibility | Cannot do |
| --- | --- | --- | --- |
| 1. Page layout analysis | `parser/layout.py` | Vector rule segments merged into collinear components; `PageLayout` owns words, blocks and components in display space | invent a table |
| 2. Table region detection | `parser/table_regions.py` | A component with >= 2 horizontal and >= 2 vertical rules, min size 70 x 15 pt, is a `TableRegion(source="rule_lattice")`. Text alignment is a fallback only when the page has no components at all | split or classify a table |
| 3. Table structure recognition | `parser/structure.py` | Rules give hard boundaries; header labels and recurring body gutters give soft boundaries; union-find merges only at boundaries where a rule is missing *and* text crosses | read header semantics |
| 4. Header / column semantics | `parser/header_semantics.py` | Header depth, per-column labels, coarse roles, table-type hypothesis, and the region evidence gate | create or delete a table |
| 5. Candidate registry | `parser/candidate_registry.py` | Binds every cell to table/row/cell/page bbox and to the roles from layer 4 | re-interpret geometry |

`parser/table_detector.py` is orchestration only: it calls the layers, decides
`reconstructed` / `partial`, and returns `DetectedTable`. It no longer contains
boundary heuristics.

## Evidence rules (layer 3)

Hard boundaries:

- A vertical rule is a column boundary only when it covers >= 55% of the table
  height and text crosses it in < 40% of row bands. This drops nested
  TEST CONDITIONS sub-boxes and rows where text runs through the line.

Soft boundaries (only when the header does not already declare the column):

- Header label runs are primary: gaps between header words become boundaries,
  including a wide-gap rule that uses the next label's left edge.
- Body gutters must recur in >= 40% of row bands and be >= 12 pt away from an
  existing boundary and produce a column >= 12 pt wide.
- A soft boundary is skipped when a hard rule lies inside the same gutter, or
  when header words occupy the interval between neighbouring boundaries.

Merging:

- Horizontal neighbours merge only at a hard boundary with vertical coverage
  < 55% and a text run crossing that boundary.
- Vertical neighbours merge only at rule-derived row boundaries with horizontal
  coverage < 55%.
- Cells keep `row_span` / `column_span`; nothing is flattened.

Layer 4 rules:

- A leading header row may be sparse (a canopy label above a wider label row);
  a second header row is accepted only when it is a label row — no cell longer
  than 40 characters and at least two header-vocabulary hits, or a merged cell.
  This separates "MIN/TYP/MAX" rows from data rows that merely contain a value.
- Section rows ("OFFSET VOLTAGE") under the header are body rows.
- Header roles are token-matched (`min`, `typ`, `max`, `unit`, `condition`,
  `symbol`), so `administrator` no longer matches `min`.
- `assess_region` keeps single-row tables and rejects a region only for
  structural evidence: no multi-column grid, no data row under the header,
  too few populated rows, numeric first row resembling a bit-field diagram,
  prose-length cells dominating, or > 25% of words unassignable to cells.

## Gold Set

- 45 tables and 19 negatives over LM358 (68 p), ADS1299 (84 p), ADC12DJ5200
  (180 p); PDF SHA256 values are in `gold/manifest.json`.
- Negatives cover prose, TOC, pin lists, chart annotations, revision history,
  timing diagrams, legal notices and bit-field diagrams.
- Annotation is independent of the production detector: proposed boxes come from
  `tools/goldset/rules.py`; every accept/reject, merge, header depth, column role
  and cross-page relation is a human decision in `gold/spec.yaml`.
- Visual proof for every item: `gold/overlays/*.png`, gallery `gold/review.html`.
- Single-row tables are explicitly counted and kept in recall (`ADC12DJ5200-P47-T01`).

## Results on the same Gold Set

Table detection:

| Metric | Baseline | After |
| --- | --- | --- |
| TP / FP / FN | 16 / 309 / 29 | 39 / 4 / 6 |
| Precision / Recall / F1 | 0.0492 / 0.3556 / 0.0865 | 0.9070 / 0.8667 / 0.8864 |
| Negative FP | 59 | 4 |
| Out-of-scope predictions | 68 | 7 |
| Mean predictions per gold table | 5.911 | 0.867 |

Structure on the 39 matched tables:

| Metric | Baseline | After |
| --- | --- | --- |
| Row count exact | 5 / 16 | 38 / 39 |
| Column count exact | 12 / 16 | 34 / 39 |
| Row and column exact | 5 / 16 | 33 / 39 |
| Header column accuracy | 0.0413 | 0.5932 |
| Header tables exact | 1 | 20 |
| Column-role accuracy | 0.0331 | 0.6398 |
| Column-role tables exact | 0 | 12 |
| Table-type accuracy | 0.0000 | 0.5128 |

Cell-text F1 (0.8655 -> 0.8302) is computed over matched tables only; the two
values cover 16 and 39 tables respectively and are not directly comparable.
All other structure metrics use the same 45-table denominator.

Physical chain unchanged: 60/60 sampled non-empty candidates across the three
PDFs still contain rendered ink at 150 dpi.

## Remaining failures (documented, not hidden)

- 6 false negatives: `ADC12DJ5200-P43-T01`, `ADC12DJ5200-P61-T02`,
  `ADC12DJ5200-P78-T03`, `ADC12DJ5200-P78-T04`, `ADC12DJ5200-P79-T01`,
  `ADS1299-P74-T01`. Five are continuation fragments without a closed rule
  lattice; one is a table whose ruling stops before its last row band.
- 4 negative false positives: three table-of-contents layouts (page 2 of LM358
  and ADC12DJ5200, two regions) and one "features" prose page in ADC12DJ5200.
  They are rule-backed layouts, so the region gate accepts them; distinguishing
  a TOC from a table needs a semantic layer that this round deliberately does
  not build.
- Column count mismatches: `ADS1299-P70-T01` (-1, missing symbol column),
  `ADS1299-P76-T01` (-2, ordering table whose wrapped header labels span two
  visual columns), `LM358-P04-T01` (-1, partial sub-rule intentionally dropped),
  `LM358-P11-T01` (+1, physical sub-rule inside TEST CONDITIONS that gold
  annotates as one column), `LM358-P33-T01` (-4, rule-less ordering table).
- Row count mismatch: `ADC12DJ5200-P47-T01` (+3, one annotated row is rendered
  as several ruled bands).

`reconstructed` remains a status, not evidence: matched tables split 19
`reconstructed` / 20 `partial`, and status does not affect the metrics above.

## Verification

```text
python -m pytest -q            -> 48 passed
python -m tools.goldset.evaluate ...   -> gold/after_report.*
python -m tools.goldset.compare ...    -> gold/comparison.md
```

## Out of scope this round

No LLM, no DashScope, no automatic parameter search, no changes to the candidate
domain schema beyond column roles and detection method, and no relaxation of
evidence rules to chase precision or recall.
