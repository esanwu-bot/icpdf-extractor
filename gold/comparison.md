# Phase 1.2 before/after on the same Gold Set

- Before: `baseline-1d8c722` (parser committed as `phase1.1-baseline`)
- After: `after-5layer-v4` (2026-11-05T14:11:49+00:00)
- Gold annotation: `gold-2026-11-05.1`

## Table detection

| Metric | Baseline | After | Delta |
| --- | --- | --- | --- |
| Gold tables | 45 | 45 | +0 |
| TP | 16 | 39 | +23 |
| FP | 309 | 4 | -305 |
| FN | 29 | 6 | -23 |
| Precision | 0.0492 | 0.9070 | +0.8578 |
| Recall | 0.3556 | 0.8667 | +0.5111 |
| F1 | 0.0865 | 0.8864 | +0.7999 |
| Negative FP | 59 | 4 | -55 |
| Out-of-scope predictions | 68 | 7 | -61 |

## Structure on matched tables

| Metric | Baseline | After | Delta |
| --- | --- | --- | --- |
| Matched tables | 16 | 39 | +23 |
| Row count exact | 5 | 38 | +33 |
| Column count exact | 12 | 34 | +22 |
| Row and column exact | 5 | 33 | +28 |
| Cell-text F1 | 0.8655 | 0.8302 | -0.0353 |
| Header column accuracy | 0.0413 | 0.5932 | +0.5519 |
| Header tables exact | 1 | 20 | +19 |
| Column-role accuracy | 0.0331 | 0.6398 | +0.6067 |
| Column-role tables exact | 0 | 12 | +12 |
| Table-type accuracy | 0.0000 | 0.5128 | +0.5128 |

## Per PDF (table detection)

| PDF | Baseline P / R / F1 | After P / R / F1 |
| --- | --- | --- |
| adc12dj5200 | 0.1408 / 0.5263 / 0.2222 | 0.8235 / 0.7368 / 0.7778 |
| ads1299 | 0.0779 / 0.4000 / 0.1304 | 1.0000 / 0.9333 / 0.9655 |
| lm358 | 0.0000 / 0.0000 / 0.0000 | 0.9167 / 1.0000 / 0.9565 |

## Fragmentation

| Metric | Baseline | After |
| --- | --- | --- |
| Mean predictions overlapping one gold table | 5.911 | 0.867 |
| Maximum overlapping predictions | 25 | 1 |

## Negative samples

| Negative kind | Baseline FP | After FP |
| --- | --- | --- |
| bit_field_diagram | 4 | 0 |
| chart_annotations | 27 | 0 |
| legal_notice | 0 | 0 |
| pin_diagram | 16 | 0 |
| prose | 8 | 1 |
| revision_history | 0 | 0 |
| timing_diagram | 1 | 0 |
| toc | 3 | 3 |

## Notes

- Cell-text F1 is computed only over matched tables, so the baseline value
  (16 matched) and the after value (39 matched) are not directly comparable;
  all other structure metrics share the same denominator.
- Header/role metrics count a table only when the predicted column count
  equals the gold column count, matching `gold/README.md`.
