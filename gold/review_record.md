# Independent review record — Phase 1.2, round 2

- Review date: 2026-11-06
- Reviewer: independent second pass (fresh context, PDF-first; parser output was not
  used to justify an annotation)
- Machine-readable statuses: `gold/independent_review.json`
- Visual evidence: `gold/overlays/*.png` (one per item) and
  `gold/review_crops/indep_*.png` (standalone crops used for the negative review)
- Result: **all 46 tables and 19 negatives reviewed; 2 corrections; 0 annotations
  rejected.** The reviewer condition "FN and FP cases, structural mismatches, and at
  least 10 TP spot checks" is exceeded: every item was reviewed.

## Method

1. Each item was re-opened on the source PDF as a standalone crop, independently of
   the annotator overlay, and judged from the printed datasheet.
2. Bbox, header depth, header text, column and row count, merges and column roles
   were checked against the printed headings.
3. The annotation overlay was compared afterwards; disagreements were classified as
   gold ambiguity, annotation debt, or parser gap.
4. Parser output was consulted last, only for that classification. No gold boundary
   or label was relaxed to make a metric pass.

## Coverage

| Scope | Count | Result |
| --- | --- | --- |
| Gold tables | 46 | 22 confirmed, 23 confirmed with a documented note, 1 added |
| Negatives | 19 | 16 confirmed, 2 confirmed with a documented note, 1 bbox corrected |
| Baseline false negatives | 30 | all are real tables; annotations confirmed |
| Baseline true-positive spot checks | 16 | all confirmed (requirement: >= 10) |
| Baseline in-scope FP | 309 | parser over-segmentation, not gold errors |
| Baseline negative FP | 59 | parser over-segmentation, not gold errors |
| Current column-count mismatches | 2 | both traced to the frozen gold convention |
| Current role-mismatch tables | 5 | 1 gold ambiguity, 1 annotation debt, 3 heuristics |

## Corrections made during this review

1. **`ADC12DJ5200-P01-T01` added.** Table 6-2 "Package Information" on page 1 was not
   in the round-1 gold set. It is a real 3-column, one-row table:
   `ADC12DJ5200SE | FCBGA (144) | 10mm x 10mm`. Its absence was the reason the p.1
   region showed up in the false-positive analysis.
2. **`ADC12DJ5200-N01-P01-FEATURES` narrowed** from `[54, 115, 560, 650]` to
   `[54, 115, 300, 660]`. The old negative box covered the table above; the negative
   now contains only the Features/Applications prose column.

Both before/after reports were regenerated on the corrected set
(`gold-2026-11-06.1`, 46 tables + 19 negatives), so the comparison still uses one
identical gold set on both sides.

## Baseline false negatives (30)

All 30 were reviewed as tables on the printed page. "Confirmed" means bbox, header
depth and column structure match the datasheet.

| Item | Page | Review note |
| --- | --- | --- |
| `ADC12DJ5200-P01-T01` | 1 | Added during review (correction 1) |
| `ADC12DJ5200-P39-T01` | 39 | Device Family Comparison, 7 columns; confirmed |
| `ADC12DJ5200-P61-T01` | 61 | JESD204C signal table, 5 columns; confirmed |
| `ADC12DJ5200-P61-T02` | 61 | Feature/support table, 4 columns; confirmed |
| `ADC12DJ5200-P72-T01` | 72 | Operating-mode configuration, 4 columns; confirmed |
| `ADC12DJ5200-P78-T01` | 78 | JMODE symbol definitions, 3 columns; confirmed |
| `ADC12DJ5200-P79-T01` | 79 | Ordinal register map continuation, 17 columns; confirmed |
| `ADC12DJ5200-P100-T01` | 100 | Register map, 4 columns; confirmed |
| `ADC12DJ5200-P102-T01` | 102 | CONFIG A field descriptions, 5 columns; confirmed |
| `ADC12DJ5200-P102-T02` | 102 | CONFIG B field descriptions, 4 columns; confirmed |
| `ADS1299-P27-T01` | 27 | CLKSEL/CLK_EN clock selection, 4 columns; confirmed |
| `ADS1299-P40-T01` | 40 | Command definitions, 5 columns; confirmed |
| `ADS1299-P44-T01` | 44 | Dense ID-register map, 11 columns; confirmed, cell text spot-checked |
| `ADS1299-P45-T01` | 45 | BIAS signal field descriptions, 5 columns; confirmed |
| `ADS1299-P52-T01` | 52 | BIAS negative-signal map, 5 columns; confirmed |
| `ADS1299-P67-T01` | 67 | EEG design requirements, 2 columns; confirmed |
| `ADS1299-P70-T01` | 70 | Timing table; gold 5 vs parser 4 columns (ambiguity 1); annotation confirmed |
| `ADS1299-P74-T01` | 74 | Related links, two-row header, 6 columns; confirmed |
| `ADS1299-P76-T01` | 76 | Rule-less ordering table, 10 logical columns; confirmed |
| `LM358-P04-T01` | 4 | Absolute maximum ratings; gold 6 vs parser 5 (ambiguity 1); annotation confirmed |
| `LM358-P04-T02` | 4 | ESD ratings, 4 columns; column 1 is an unlabeled condition column (ambiguity 2) |
| `LM358-P05-T01` | 5 | Recommended operating conditions, 5 columns; confirmed |
| `LM358-P05-T02` | 5 | Thermal information, three-row header, 10 columns; confirmed |
| `LM358-P06-T01` | 6 | Electrical characteristics, 7 columns; confirmed |
| `LM358-P08-T01` | 8 | Electrical characteristics, 7 columns (TEST CONDITIONS sub-boxes stay one column); confirmed |
| `LM358-P10-T01` | 10 | Electrical characteristics, 6 columns; confirmed |
| `LM358-P11-T01` | 11 | Electrical characteristics, 6 columns; confirmed |
| `LM358-P12-T01` | 12 | Electrical characteristics, 6 columns; confirmed |
| `LM358-P14-T01` | 14 | Electrical characteristics, 6 columns; confirmed |
| `LM358-P33-T01` | 33 | Rule-less ordering table, 10 logical columns; confirmed |

## True-positive spot checks (16 baseline TPs, plus the added P01)

`ADS1299-P17-T01/T02/T03` (canopy headers, 13/13/8 columns),
`ADS1299-P23-T01` (GAIN vs bandwidth, 2), `ADS1299-P35-T01` (DR timing, 3),
`ADS1299-P37-T01` (timing, gold merged partial band; ambiguity 1),
`ADC12DJ5200-P41-T01` (sample-code comparison, 4), `ADC12DJ5200-P43-T01` (clock
mode, 3), `ADC12DJ5200-P46-T01` (two-row header with vertical merge, 4),
`ADC12DJ5200-P47-T01` (PFIR modes, 6), `ADC12DJ5200-P54-T01` (NCO_RDIV, 2),
`ADC12DJ5200-P78-T02/T03/T04` (ordinal headers, 17), `ADC12DJ5200-P98-T01`
(register map, 4), `ADC12DJ5200-P102-T03` (CHIP_TYPE, 3). All confirmed. The newly
added `ADC12DJ5200-P01-T01` (package information) was reviewed as part of the
correction above.

## Negative review (19)

| Kind | Items | Result |
| --- | --- | --- |
| prose | LM358-N01, ADS1299-N01/N03, ADC12DJ5200-N01 | No table grid; N01 bbox corrected |
| toc | LM358-N02, ADS1299-N02, ADC12DJ5200-N02 | Dot-leader contents lists; confirmed |
| pin_diagram | LM358-N03, ADS1299-N04, ADC12DJ5200-N03 | Pinout graphics; confirmed |
| chart_annotations | LM358-N04, ADS1299-N05, ADC12DJ5200-N04 | Plot axes/legend text; confirmed |
| revision_history | LM358-N05 | Text block without grid; confirmed |
| timing_diagram | ADS1299-N06 | Power-up waveform; confirmed |
| legal_notice | ADS1299-N07, ADC12DJ5200-N06 | Prose/legal text; confirmed |
| bit_field_diagram | ADC12DJ5200-N05/N07 | Single-row register bit-field diagrams; out of data-table scope (ambiguity 4) |

## False-positive review

The baseline's 309 in-scope FP and 59 negative FP are **parser artifacts, not gold
errors**. The baseline emits 5.783 predictions per gold table on average (maximum
25) and fragments ruled boxes across every page; the annotations that produced those
FPs were reconfirmed here item by item. After the five-layer rewrite the same gold
set yields 0 in-scope FP and 0 negative FP without any annotation being relaxed.

## Structural mismatches in the current round

### Column count (2)

- `ADS1299-P70-T01`: gold 5, parser 4 — partial "Either input" band split (ambiguity 1).
- `LM358-P04-T01`: gold 6, parser 5 — same band, same convention (ambiguity 1).

### Column roles (5 tables, 3 of 292 columns wrong)

| Item | Gold | Predicted | Classification |
| --- | --- | --- | --- |
| `ADC12DJ5200-P46-T01` | value... | symbol... | gold ambiguity 3 (SYSREF bit-field lead) |
| `ADS1299-P27-T01` | condition at col 1 | value | parser gap: `CONFIG1.CLK_EN BIT` |
| `ADS1299-P70-T01` | 5 roles | 4 roles | consequence of the column split (ambiguity 1) |
| `LM358-P04-T01` | 6 roles | 5 roles | consequence of the column split (ambiguity 1) |
| `LM358-P04-T02` | condition at col 1 | unknown | annotation debt 2 (blank header) |

Role accuracy is 0.9897 (289/292 columns); MIN, TYP, MAX, UNIT and SYMBOL have
recall 1.0, CONDITION 0.9091, VALUE 0.9951.

### Header

No compact header-text mismatches across the 44 comparable tables (287 labeled
columns). The strict-spacing variant is 0.9582 because extraction inserts spaces
inside `fCLK` and `µV` (`f CLK`, `µ V RMS`); 12 columns in `ADC12DJ5200-P43-T01`,
`ADC12DJ5200-P54-T01` and `ADS1299-P17-T01/T02/T03` are affected and the compact
comparison treats them as equal. Header row depth is exact on 46/46 tables and all
10 multi-layer headers are exact; `header_path` is present on all 46.

## Open gold ambiguities (kept frozen for comparability)

1. **Partial condition column.** `LM358-P04-T01` and `ADS1299-P70-T01` split the
   partial "Either input" band into two columns; `ADS1299-P37-T01` merges the same
   band. The gold set is internally inconsistent. A future annotation revision must
   pick one convention; this round keeps both so before/after stay comparable.
2. **Unlabeled condition column.** `LM358-P04-T02` prints no header over its
   test-condition column; the parser reports `unknown` rather than guessing.
3. **Leading SYSREF column.** `ADC12DJ5200-P46-T01` annotates the leading
   `SYSREF_POS[23:0] | ...` column as `value`; the parser's leading-column heuristic
   calls it `symbol`.
4. **Bit-field negatives.** `ADC12DJ5200-N05/N07` are single-row register diagrams
   that look table-like. They are excluded from data-table scope by design; the
   parser agrees.
5. **Dense register maps.** `ADS1299-P44-T01`, `ADC12DJ5200-P98/P100` were verified
   structurally; cell text was spot-checked, not verified cell by cell.

## Metric denominators

Defined in `gold/README.md` and repeated in `gold/comparison.md`:

- Detection: precision = TP / (TP + in-scope FP); recall = TP / (TP + FN).
- Row / column count: matched tables.
- Cell text: cell multiset over matched tables.
- Header column attribution: labeled gold columns of tables whose predicted column
  count equals gold (baseline 5 columns on 1 table; after 287 columns on 44 tables).
- Header row depth: matched tables; multi-layer: tables with gold header depth >= 2.
- Role: comparable columns; MIN/TYP/MAX/UNIT/CONDITION/SYMBOL/VALUE reported
  separately with a confusion-free per-role P/R/F1 table.

## Verification

```text
python -m pytest -q                                   -> 48 passed
python -m tools.goldset.evaluate ... (round 10)       -> 46 TP / 0 FP / 0 FN, 0 negative FP
python -m tools.goldset.compare ...                   -> gold/comparison.md
```

The machine-readable item statuses in `gold/independent_review.json` are merged into
`gold/gold_table_set.jsonl` and summarized in `gold/manifest.json`
(`items_reviewed: 65`, `items_pending: 0`).
