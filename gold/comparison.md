# Phase 1.2 before/after on the same Gold Set

- Before: `baseline-1d8c722` (parser committed as `phase1.1-baseline`)
- After: `after-5layer-v5` (2026-11-05T18:18:11+00:00)
- Gold annotation: `gold-2026-11-06.1`

## Table detection

| Metric | Baseline | After | Delta |
| --- | --- | --- | --- |
| Gold tables | 46 | 46 | +0 |
| TP | 16 | 46 | +30 |
| FP | 309 | 0 | -309 |
| FN | 30 | 0 | -30 |
| Precision | 0.0492 | 1.0000 | +0.9508 |
| Recall | 0.3478 | 1.0000 | +0.6522 |
| F1 | 0.0863 | 1.0000 | +0.9137 |
| Negative FP | 59 | 0 | -59 |
| Out-of-scope predictions | 68 | 8 | -60 |

## Structure on matched tables

| Metric | Baseline | After | Delta |
| --- | --- | --- | --- |
| Matched tables | 16 | 46 | +30 |
| Row count exact | 5 | 46 | +41 |
| Column count exact | 12 | 44 | +32 |
| Row and column exact | 5 | 44 | +39 |
| Cell-text F1 | 0.8655 | 0.8889 | +0.0234 |
| Header comparable tables | 1 | 44 | +43 |
| Header comparable columns | 5 | 287 | +282 |
| Header column accuracy | 1.0000 | 1.0000 | +0.0000 |
| Header column accuracy (strict spacing) | 1.0000 | 0.9582 | -0.0418 |
| Header row-depth exact | 0 | 46 | +46 |
| Header tables exact | 1 | 44 | +43 |
| Header multi-layer exact | 0 | 10 | +10 |
| Header cell-text F1 | 1.0000 | 1.0000 | +0.0000 |
| Column-role accuracy | 0.8000 | 0.9897 | +0.1897 |
| Column-role columns | 5 | 292 | +287 |
| Column-role tables exact | 0 | 41 | +41 |
| Table-type accuracy | 0.0000 | 0.5870 | +0.5870 |

## Per PDF (table detection)

| PDF | Baseline P / R / F1 | After P / R / F1 |
| --- | --- | --- |
| adc12dj5200 | 0.1408 / 0.5000 / 0.2198 | 1.0000 / 1.0000 / 1.0000 |
| ads1299 | 0.0779 / 0.4000 / 0.1304 | 1.0000 / 1.0000 / 1.0000 |
| lm358 | 0.0000 / 0.0000 / 0.0000 | 1.0000 / 1.0000 / 1.0000 |

## Fragmentation

| Metric | Baseline | After |
| --- | --- | --- |
| Mean predictions overlapping one gold table | 5.783 | 1.0 |
| Maximum overlapping predictions | 25 | 1 |

## Negative samples

| Negative kind | Baseline FP | After FP |
| --- | --- | --- |
| bit_field_diagram | 4 | 0 |
| chart_annotations | 27 | 0 |
| legal_notice | 0 | 0 |
| pin_diagram | 16 | 0 |
| prose | 8 | 0 |
| revision_history | 0 | 0 |
| timing_diagram | 1 | 0 |
| toc | 3 | 0 |

## Metric denominators

| Metric family | Denominator |
| --- | --- |
| Detection precision | TP / (TP + in-scope FP) |
| Detection recall | TP / (TP + FN); every accepted gold table counts |
| Row count exact | matched tables whose predicted row count equals gold |
| Column count exact | matched tables whose predicted column count equals gold |
| Cell-text F1 | cell multiset over the cells of matched tables |
| Header column accuracy | columns with equal compact label / labeled gold columns of comparable tables |
| Header column accuracy (strict) | same denominator, exact spacing |
| Header row depth | matched tables with equal header_rows |
| Header tables exact | comparable tables with every labeled column exact |
| Header multi-layer | matched tables whose gold header_rows >= 2 |
| Header cell-text F1 | labeled header cells of comparable tables |
| Column role | columns with equal coarse role / comparable columns |
| Table type | matched tables with equal table_type |

## Notes

- Cell-text F1 is computed over matched tables (16 baseline, 46 after), so those values are not directly comparable.
- Header column attribution and column-role accuracy are scored only on tables whose predicted column count equals gold: 1 table(s) / 5 column(s) baseline versus 44 tables / 287 columns after. The baseline had no header model, so its accuracy values rest on a much smaller denominator and must be read with those counts.
- Table-type accuracy uses matched tables as the denominator; the per-class confusion matrix is in `gold/after_report.md`.
