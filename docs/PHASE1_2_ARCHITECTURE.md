# Phase 1.2 — Gold Set and five-layer detector

Status: Phase 1.2 round 2 approved by the reviewer.  Phase 1.3 evidence-chain
work is in progress (`docs/PHASE1_3_EVIDENCE.md`); Phase 2 (LLM) remains frozen.

Baseline for every number in this document: commit
`1d8c7220601db734b63437abd41c36739a42aa89` (tag `phase1.1-baseline`),
evaluated on `gold/gold_table_set.jsonl` (annotation `gold-2026-11-06.1`,
46 tables + 19 negatives, all independently reviewed).
After numbers: `gold/after_report.json` (`after-5layer-v5`), same Gold Set.
Delta and metric denominators: `gold/comparison.md`.
Independent review: `gold/review_record.md` and `gold/independent_review.json`.

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

- Header depth is inferred from evidence, not position: header vocabulary,
  column canopies, ordinal rows (`OCTET | 0 | 1 | ...`), sparse lead rows above a
  label row, tabular first rows, vertically merged cells (a label spanning rows
  0-1), and a third row only when it is a real label row across at least half the
  columns (pin counts), never a lone section banner.
- A leading header row may be sparse (a canopy label above a wider label row);
  a second header row is accepted only when it is a label row — no cell longer
  than 40 characters and at least two header-vocabulary hits, or a merged cell.
  This separates "MIN/TYP/MAX" rows from data rows that merely contain a value.
- Canopy labels propagate down a column only when the column has no lower label;
  the leading row-header column is never overwritten by a device-list canopy.
- Ordinal group headers (`0 1 2 3...` over register nibbles) are spread evenly
  across the data columns instead of trusting inconsistent drawn spans.
- Section rows ("OFFSET VOLTAGE") under the header are body rows.
- Header roles are token-matched (`min`, `typ`, `max`, `unit`, `condition`,
  `symbol`), so `administrator` no longer matches `min`. Limit words only name a
  limit column in short labels (`MAX`, not `MAXIMUM SAMPLING RATE`); selector
  labels (`MODE`, `CLOCK SOURCE`, `REFERENCE CLAUSE`, package options such as
  `D (SOIC)`) are conditions; a leading column is a symbol unless it is a
  part-number/address/bit/sample-code column or names a stimulus with a unit.
  An unlabeled column left of the limit columns is a condition column.
- `assess_region` keeps single-row tables and rejects a region only for
  structural evidence: no multi-column grid, no data row under the header,
  too few populated rows, numeric first row resembling a bit-field diagram,
  prose-length cells dominating, or > 25% of words unassignable to cells.

## Gold Set

- 46 tables and 19 negatives over LM358 (68 p), ADS1299 (84 p), ADC12DJ5200
  (180 p); PDF SHA256 values are in `gold/manifest.json`.
- Negatives cover prose, TOC, pin lists, chart annotations, revision history,
  timing diagrams, legal notices and bit-field diagrams.
- Annotation is independent of the production detector: proposed boxes come from
  `tools/goldset/rules.py`; every accept/reject, merge, header depth, column role
  and cross-page relation is a human decision in `gold/spec.yaml`.
- Visual proof for every item: `gold/overlays/*.png`, gallery `gold/review.html`.
- **Independent review is complete**: all 46 tables and 19 negatives were
  re-opened on the PDF (65/65 items reviewed, 0 pending). Two corrections were
  applied (`ADC12DJ5200-P01-T01` added, `ADC12DJ5200-N01-P01-FEATURES` narrowed);
  both sides of the comparison were re-run on the corrected set. Open gold
  ambiguities are frozen and listed in `gold/review_record.md`.
- Single-row tables are explicitly counted and kept in recall (`ADC12DJ5200-P47-T01`).

## Results on the same Gold Set

Table detection:

| Metric | Baseline | After |
| --- | --- | --- |
| TP / FP / FN | 16 / 309 / 30 | 46 / 0 / 0 |
| Precision / Recall / F1 | 0.0492 / 0.3478 / 0.0863 | 1.0000 / 1.0000 / 1.0000 |
| Negative FP | 59 | 0 |
| Out-of-scope predictions | 68 | 8 |
| Mean predictions per gold table | 5.783 | 1.000 |

Structure on the 46 matched tables:

| Metric | Baseline | After |
| --- | --- | --- |
| Row count exact | 5 / 16 | 46 / 46 |
| Column count exact | 12 / 16 | 44 / 46 |
| Row and column exact | 5 / 16 | 44 / 46 |
| Header row depth exact | 0 / 16 | 46 / 46 |
| Header column accuracy (compact) | 1.0000 (1 table, 5 cols) | 1.0000 (44 tables, 287 cols) |
| Header column accuracy (strict spacing) | 1.0000 (1 table, 5 cols) | 0.9582 (44 tables, 287 cols) |
| Header tables exact | 1 / 1 comparable | 44 / 44 comparable |
| Multi-layer header exact | 0 / 7 | 10 / 10 |
| Header cell-text F1 | 1.0000 (5 cells) | 1.0000 (287 cells) |
| Column-role accuracy | 0.8000 (5 cols) | 0.9897 (292 cols) |
| Column-role tables exact | 0 | 41 |
| Table-type accuracy | 0.0000 | 0.5870 |

Cell-text F1 0.8655 -> 0.8889 is computed over matched tables only (16 vs 46),
so it is not directly comparable. The baseline header/role accuracies rest on the
single table that had a comparable header, so they must be read with their
denominators; `gold/comparison.md` prints them explicitly.

Physical chain unchanged: 60/60 sampled non-empty candidates across the three
PDFs still contain rendered ink at 150 dpi.

## Remaining failures (documented, not hidden)

- Detection: 0 FP, 0 FN, 0 negative FP. Eight predictions remain out of scope
  (page areas outside annotated regions); gold is page-sampled, so they are
  reported but not scored.
- Column count (2): `ADS1299-P70-T01` and `LM358-P04-T01` each miss one column
  because gold splits the partial "Either input" band while the parser merges it.
  The gold set is itself inconsistent here (`ADS1299-P37-T01` merges the band);
  fixing it needs an annotation revision, not a parser change.
- Column roles (3 of 292 columns wrong): `ADS1299-P27-T01` misses the
  `CONFIG1.CLK_EN BIT` condition; `ADC12DJ5200-P46-T01` calls the leading SYSREF
  bit-field column `symbol` where gold says `value`; `LM358-P04-T02` leaves its
  blank condition column `unknown`. `ADS1299-P70-T01` / `LM358-P04-T01` role
  differences are consequences of the column split.
- Header labels: no compact mismatches. The strict-spacing variant differs on 12
  columns of `ADC12DJ5200-P43-T01`, `ADC12DJ5200-P54-T01` and
  `ADS1299-P17-T01/T02/T03` because extraction spaces `fCLK` as `f CLK` and
  `µV` as `µ V`.

`reconstructed` remains a status, not evidence: matched tables split 30
`reconstructed` / 16 `partial`, and status does not affect the metrics above.

## Verification

```text
python -m pytest -q                    -> 48 passed
python -m tools.goldset.evaluate ...   -> gold/after_report.*
python -m tools.goldset.compare ...    -> gold/comparison.md
```

## Out of scope this round

No LLM, no DashScope, no automatic parameter search, no changes to the candidate
domain schema beyond column roles and detection method, and no relaxation of
evidence rules to chase precision or recall.
