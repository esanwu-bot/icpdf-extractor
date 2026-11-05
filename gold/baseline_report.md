# Gold Set evaluation: baseline-1d8c722

- Gold annotation: `gold-2026-11-06.1`
- Baseline: `phase1.1-baseline` at `1d8c7220601db734b63437abd41c36739a42aa89`
- Generated: 2026-11-05T18:17:17+00:00
- Matching: one-to-one per page, IoU >= 0.5; in-scope FP when overlap/prediction >= 0.25
- Scope: prediction must overlap an annotated table or negative region

## Gold set composition

| PDF | Tables | Negatives |
| --- | --- | --- |
| adc12dj5200 | 20 | 7 |
| ads1299 | 15 | 7 |
| lm358 | 11 | 5 |

Table types: {'absolute_maximum': 2, 'electrical_characteristics': 15, 'ordering_information': 3, 'other': 22, 'pin_functions': 2, 'recommended_operating': 1, 'thermal': 1}

## Runs

| PDF | Run | Parser config SHA256 |
| --- | --- | --- |
| adc12dj5200 | `20261105T124735Z-1ab90a` | `e582fa62efbef6b816095e4e7a972a88e2ed40f8c4578c8dacacb5ea43f6f98a` |
| ads1299 | `20261105T124706Z-b154f5` | `e582fa62efbef6b816095e4e7a972a88e2ed40f8c4578c8dacacb5ea43f6f98a` |
| lm358 | `20261105T124640Z-16e592` | `e582fa62efbef6b816095e4e7a972a88e2ed40f8c4578c8dacacb5ea43f6f98a` |

## Overall table detection

| Gold tables | TP | FP | FN | Precision | Recall | F1 | Out-of-scope predictions | Predictions on gold pages |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 46 | 16 | 309 | 30 | 0.0492 | 0.3478 | 0.0863 | 68 | 393 |

## Per PDF

| PDF | Gold | TP | FP | FN | Precision | Recall | F1 | Out-of-scope | Predictions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adc12dj5200 | 20 | 10 | 61 | 10 | 0.1408 | 0.5000 | 0.2198 | 10 | 81 |
| ads1299 | 15 | 6 | 71 | 9 | 0.0779 | 0.4000 | 0.1304 | 22 | 99 |
| lm358 | 11 | 0 | 177 | 11 | 0.0000 | 0.0000 | 0.0000 | 36 | 213 |

## Over-detection / fragmentation

- Predictions on gold pages: 393
- In-scope false positives: 309
- Out-of-scope predictions (unannotated page area): 68
- Mean predictions overlapping one gold table: 5.783
- Maximum predictions overlapping one gold table: 25 (LM358-P10-T01, LM358-P14-T01)
- Overlap-count distribution: {'0': 3, '1': 17, '2': 1, '3': 8, '4': 2, '5': 1, '8': 3, '9': 1, '10': 1, '12': 1, '13': 2, '18': 2, '19': 1, '24': 1, '25': 2}

## Structure on matched tables

| Metric | Value |
| --- | --- |
| Matched tables | 16 |
| Row count exact | 5 |
| Column count exact | 12 |
| Row and column exact | 5 |
| Cell-text F1 | 0.8655 |
| Header column accuracy | 1.0000 |
| Header column accuracy (strict spacing) | 1.0000 |
| Header row-depth exact | 0 | (of 16 matched) |
| Header tables exact | 1 | (of 1 comparable) |
| Header cell-text F1 | 1.0000 |
| Multi-layer header exact | 0 | (of 7) |
| Tables carrying header_path | 0 |
| Column-role accuracy | 0.8000 |
| Column-role tables exact | 0 |
| Table-type accuracy | 0.0000 |
| Reconstruction status (matched) | {'partial': 6, 'reconstructed': 10} |
| Row error distribution | {'-2': 3, '-1': 5, '0': 5, '1': 2, '2': 1} |
| Column error distribution | {'-10': 3, '0': 12, '1': 1} |

## Metric denominators

| Metric family | Denominator |
| --- | --- |
| detection_precision | TP + in-scope FP (predictions on annotated pages) |
| detection_recall | TP + FN (accepted gold tables) |
| row_count | 16 matched tables |
| column_count | 16 matched tables |
| cell_text | matched tables; multiset F1 over non-empty cell texts |
| header_cell_text | 1 matched tables with equal column count; multiset F1 over non-empty header labels, whitespace-free |
| header_column_attribution | 5 labelled gold header columns (empty gold labels excluded) in 1 comparable matched tables; strict variant keeps intra-label spacing |
| header_multilayer | 7 matched gold tables with header_rows >= 2 |
| header_row_detection | header_rows exact over all matched tables |
| column_role | 5 gold columns in comparable matched tables |

## Column roles by role

| Role | Gold columns | Predicted columns | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| min | 0 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| typ | 0 | 1 | 0 | 1 | 0 | 0.0000 | 0.0000 | 0.0000 |
| max | 0 | 0 | 0 | 0 | 0 | 0.0000 | 0.0000 | 0.0000 |
| unit | 1 | 0 | 0 | 0 | 1 | 0.0000 | 0.0000 | 0.0000 |
| condition | 1 | 0 | 0 | 0 | 1 | 0.0000 | 0.0000 | 0.0000 |
| symbol | 8 | 0 | 0 | 0 | 8 | 0.0000 | 0.0000 | 0.0000 |
| value | 57 | 4 | 4 | 0 | 53 | 1.0000 | 0.0702 | 0.1311 |
| unknown | 0 | 62 | 0 | 62 | 0 | 0.0000 | 0.0000 | 0.0000 |

## Confusion matrices

### table_type

| gold \ pred | absolute_maximum | recommended_operating | electrical_characteristics | thermal | pin_functions | ordering_information | other | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| absolute_maximum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| recommended_operating | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| electrical_characteristics | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| thermal | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| pin_functions | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ordering_information | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| other | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| unknown | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### header_rows

| gold \ pred | 0 | 1 | 2 | 3 | 4 |
| --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 9 | 0 | 0 | 0 | 0 |
| 2 | 7 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 |
| 4 | 0 | 0 | 0 | 0 | 0 |

### column_role

| gold \ pred | min | typ | max | unit | condition | symbol | value | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| min | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| typ | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| max | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| unit | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| condition | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| symbol | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| value | 0 | 1 | 0 | 0 | 0 | 0 | 4 | 52 |
| unknown | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Error cases

- Missed tables (FN): 30
- In-scope false positives: 309
- Row-count mismatches: 11
- Column-count mismatches: 4
- Header-text mismatches: 0
- Column-role mismatches: 16

| Case | Item | Page | Detail |
| --- | --- | --- | --- |
| FN | ADC12DJ5200-P01-T01 | 1 | gold 2 x 3, best IoU 0.0484 |
| FN | ADC12DJ5200-P39-T01 | 39 | gold 8 x 7, best IoU 0.3392 |
| FN | ADC12DJ5200-P61-T01 | 61 | gold 6 x 5, best IoU 0.0000 |
| FN | ADC12DJ5200-P61-T02 | 61 | gold 14 x 4, best IoU 0.1052 |
| FN | ADC12DJ5200-P72-T01 | 72 | gold 8 x 4, best IoU 0.0000 |
| FN | ADC12DJ5200-P78-T01 | 78 | gold 7 x 3, best IoU 0.2760 |
| FN | ADC12DJ5200-P79-T01 | 79 | gold 5 x 17, best IoU 0.4884 |
| FN | ADC12DJ5200-P100-T01 | 100 | gold 38 x 4, best IoU 0.2682 |
| FN | ADC12DJ5200-P102-T01 | 102 | gold 6 x 5, best IoU 0.1387 |
| FN | ADC12DJ5200-P102-T02 | 102 | gold 3 x 5, best IoU 0.2023 |
| FN | ADS1299-P27-T01 | 27 | gold 4 x 4, best IoU 0.3978 |
| FN | ADS1299-P40-T01 | 40 | gold 14 x 4, best IoU 0.2494 |
| FN | ADS1299-P44-T01 | 44 | gold 31 x 11, best IoU 0.2003 |
| FN | ADS1299-P45-T01 | 45 | gold 5 x 5, best IoU 0.0338 |
| FN | ADS1299-P52-T01 | 52 | gold 9 x 5, best IoU 0.0133 |
| FN | ADS1299-P67-T01 | 67 | gold 5 x 2, best IoU 0.4559 |
| FN | ADS1299-P70-T01 | 70 | gold 3 x 5, best IoU 0.3632 |
| FN | ADS1299-P74-T01 | 74 | gold 4 x 6, best IoU 0.4994 |
| FN | ADS1299-P76-T01 | 76 | gold 15 x 10, best IoU 0.1709 |
| FN | LM358-P04-T01 | 4 | gold 17 x 6, best IoU 0.1437 |
| FN | LM358-P04-T02 | 4 | gold 7 x 4, best IoU 0.2333 |
| FN | LM358-P05-T01 | 5 | gold 10 x 5, best IoU 0.2391 |
| FN | LM358-P05-T02 | 5 | gold 9 x 10, best IoU 0.1383 |
| FN | LM358-P06-T01 | 6 | gold 51 x 7, best IoU 0.0894 |
| FN | LM358-P08-T01 | 8 | gold 52 x 7, best IoU 0.0877 |
| FN | LM358-P10-T01 | 10 | gold 50 x 6, best IoU 0.0891 |
| FN | LM358-P11-T01 | 11 | gold 46 x 6, best IoU 0.1329 |
| FN | LM358-P12-T01 | 12 | gold 47 x 6, best IoU 0.0546 |
| FN | LM358-P14-T01 | 14 | gold 50 x 6, best IoU 0.0507 |
| FN | LM358-P33-T01 | 33 | gold 16 x 10, best IoU 0.0886 |
| FP | p001-t01 | 1 | table overlap 0.000, negative overlap 0.488 |
| FP | p001-t02 | 1 | table overlap 0.000, negative overlap 0.485 |
| FP | p001-t03 | 1 | table overlap 0.049, negative overlap 0.401 |
| FP | p002-t01 | 2 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t01 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t02 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t03 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t04 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t05 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t06 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t07 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t08 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t09 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t10 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t11 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t12 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t13 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p029-t14 | 29 | table overlap 0.000, negative overlap 1.000 |
| FP | p039-t01 | 39 | table overlap 1.000, negative overlap 0.000 |
| FP | p039-t02 | 39 | table overlap 1.000, negative overlap 0.000 |
| FP | p039-t03 | 39 | table overlap 1.000, negative overlap 0.000 |
| FP | p039-t04 | 39 | table overlap 1.000, negative overlap 0.000 |
| FP | p039-t05 | 39 | table overlap 1.000, negative overlap 0.000 |
| FP | p039-t06 | 39 | table overlap 1.000, negative overlap 0.000 |
| FP | p039-t07 | 39 | table overlap 1.000, negative overlap 0.000 |
| FP | p039-t08 | 39 | table overlap 1.000, negative overlap 0.000 |
| FP | p061-t01 | 61 | table overlap 1.000, negative overlap 0.000 |
| FP | p061-t02 | 61 | table overlap 1.000, negative overlap 0.000 |
| FP | p061-t03 | 61 | table overlap 1.000, negative overlap 0.000 |
| FP | p078-t01 | 78 | table overlap 1.000, negative overlap 0.000 |
| FP | p078-t02 | 78 | table overlap 1.000, negative overlap 0.000 |
| FP | p078-t03 | 78 | table overlap 1.000, negative overlap 0.000 |
| FP | p078-t05 | 78 | table overlap 1.000, negative overlap 0.000 |
| FP | p078-t06 | 78 | table overlap 1.000, negative overlap 0.000 |
| FP | p078-t08 | 78 | table overlap 1.000, negative overlap 0.000 |
| FP | p078-t09 | 78 | table overlap 1.000, negative overlap 0.000 |
| FP | p079-t01 | 79 | table overlap 1.000, negative overlap 0.000 |
| FP | p079-t02 | 79 | table overlap 1.000, negative overlap 0.000 |
| FP | p079-t03 | 79 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t01 | 100 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t02 | 100 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t03 | 100 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t04 | 100 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t05 | 100 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t06 | 100 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t07 | 100 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t08 | 100 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t09 | 100 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t10 | 100 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t11 | 100 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t12 | 100 | table overlap 1.000, negative overlap 0.000 |
| FP | p100-t13 | 100 | table overlap 0.885, negative overlap 0.000 |
| FP | p102-t01 | 102 | table overlap 1.000, negative overlap 0.000 |
| FP | p102-t02 | 102 | table overlap 1.000, negative overlap 0.000 |
| FP | p102-t03 | 102 | table overlap 1.000, negative overlap 0.000 |
| FP | p102-t04 | 102 | table overlap 1.000, negative overlap 0.000 |
| FP | p102-t05 | 102 | table overlap 0.000, negative overlap 1.000 |
| FP | p102-t06 | 102 | table overlap 0.000, negative overlap 1.000 |
| FP | p102-t07 | 102 | table overlap 1.000, negative overlap 0.000 |
| FP | p102-t08 | 102 | table overlap 0.000, negative overlap 1.000 |
| FP | p102-t09 | 102 | table overlap 0.000, negative overlap 1.000 |
| FP | p001-t02 | 1 | table overlap 0.000, negative overlap 0.488 |
| FP | p001-t03 | 1 | table overlap 0.000, negative overlap 0.498 |
| FP | p001-t04 | 1 | table overlap 0.000, negative overlap 0.488 |
| FP | p002-t01 | 2 | table overlap 0.000, negative overlap 1.000 |
| FP | p002-t02 | 2 | table overlap 0.000, negative overlap 1.000 |
| FP | p016-t01 | 16 | table overlap 0.000, negative overlap 0.359 |
| FP | p016-t02 | 16 | table overlap 0.000, negative overlap 1.000 |
| FP | p017-t01 | 17 | table overlap 1.000, negative overlap 0.000 |
| FP | p017-t02 | 17 | table overlap 1.000, negative overlap 0.000 |
| FP | p017-t04 | 17 | table overlap 1.000, negative overlap 0.000 |
| FP | p017-t05 | 17 | table overlap 1.000, negative overlap 0.000 |
| FP | p019-t01 | 19 | table overlap 0.000, negative overlap 1.000 |
| FP | p019-t02 | 19 | table overlap 0.000, negative overlap 1.000 |
| FP | p019-t03 | 19 | table overlap 0.000, negative overlap 1.000 |
| FP | p019-t04 | 19 | table overlap 0.000, negative overlap 1.000 |
| FP | p019-t05 | 19 | table overlap 0.000, negative overlap 1.000 |
| FP | p019-t06 | 19 | table overlap 0.000, negative overlap 1.000 |
| FP | p019-t07 | 19 | table overlap 0.000, negative overlap 1.000 |
| FP | p019-t08 | 19 | table overlap 0.000, negative overlap 1.000 |
| FP | p019-t09 | 19 | table overlap 0.000, negative overlap 1.000 |
| FP | p026-t01 | 26 | table overlap 0.000, negative overlap 1.000 |
| FP | p026-t02 | 26 | table overlap 0.000, negative overlap 1.000 |
| FP | p026-t03 | 26 | table overlap 0.000, negative overlap 1.000 |
| FP | p026-t04 | 26 | table overlap 0.000, negative overlap 1.000 |
| FP | p026-t05 | 26 | table overlap 0.000, negative overlap 1.000 |
| FP | p026-t06 | 26 | table overlap 0.000, negative overlap 1.000 |
| FP | p026-t07 | 26 | table overlap 0.000, negative overlap 1.000 |
| FP | p026-t08 | 26 | table overlap 0.000, negative overlap 1.000 |
| FP | p026-t09 | 26 | table overlap 0.000, negative overlap 1.000 |
| FP | p026-t10 | 26 | table overlap 0.000, negative overlap 1.000 |
| FP | p027-t01 | 27 | table overlap 0.596, negative overlap 0.000 |
| FP | p040-t01 | 40 | table overlap 1.000, negative overlap 0.000 |
| FP | p040-t02 | 40 | table overlap 1.000, negative overlap 0.000 |
| FP | p040-t03 | 40 | table overlap 0.620, negative overlap 0.000 |
| FP | p044-t01 | 44 | table overlap 1.000, negative overlap 0.000 |
| FP | p044-t02 | 44 | table overlap 1.000, negative overlap 0.000 |
| FP | p044-t03 | 44 | table overlap 1.000, negative overlap 0.000 |
| FP | p044-t04 | 44 | table overlap 1.000, negative overlap 0.000 |
| FP | p044-t05 | 44 | table overlap 1.000, negative overlap 0.000 |
| FP | p044-t06 | 44 | table overlap 1.000, negative overlap 0.000 |
| FP | p044-t07 | 44 | table overlap 1.000, negative overlap 0.000 |
| FP | p044-t08 | 44 | table overlap 1.000, negative overlap 0.000 |
| FP | p044-t09 | 44 | table overlap 1.000, negative overlap 0.000 |
| FP | p044-t10 | 44 | table overlap 1.000, negative overlap 0.000 |
| FP | p044-t11 | 44 | table overlap 1.000, negative overlap 0.000 |
| FP | p044-t12 | 44 | table overlap 1.000, negative overlap 0.000 |
| FP | p045-t03 | 45 | table overlap 1.000, negative overlap 0.000 |
| FP | p045-t04 | 45 | table overlap 1.000, negative overlap 0.000 |
| FP | p045-t05 | 45 | table overlap 1.000, negative overlap 0.000 |
| FP | p045-t06 | 45 | table overlap 1.000, negative overlap 0.000 |
| FP | p052-t02 | 52 | table overlap 1.000, negative overlap 0.000 |
| FP | p052-t03 | 52 | table overlap 1.000, negative overlap 0.000 |
| FP | p052-t04 | 52 | table overlap 1.000, negative overlap 0.000 |
| FP | p052-t05 | 52 | table overlap 1.000, negative overlap 0.000 |
| FP | p052-t06 | 52 | table overlap 1.000, negative overlap 0.000 |
| FP | p052-t07 | 52 | table overlap 1.000, negative overlap 0.000 |
| FP | p052-t08 | 52 | table overlap 1.000, negative overlap 0.000 |
| FP | p052-t09 | 52 | table overlap 1.000, negative overlap 0.000 |
| FP | p067-t07 | 67 | table overlap 0.669, negative overlap 0.000 |
| FP | p070-t02 | 70 | table overlap 0.000, negative overlap 0.685 |
| FP | p070-t03 | 70 | table overlap 0.488, negative overlap 0.000 |
| FP | p074-t02 | 74 | table overlap 1.000, negative overlap 0.000 |
| FP | p076-t01 | 76 | table overlap 1.000, negative overlap 0.000 |
| FP | p076-t02 | 76 | table overlap 1.000, negative overlap 0.000 |
| FP | p076-t03 | 76 | table overlap 1.000, negative overlap 0.000 |
| FP | p076-t04 | 76 | table overlap 1.000, negative overlap 0.000 |
| FP | p076-t05 | 76 | table overlap 1.000, negative overlap 0.000 |
| FP | p076-t06 | 76 | table overlap 1.000, negative overlap 0.000 |
| FP | p076-t07 | 76 | table overlap 1.000, negative overlap 0.000 |
| FP | p076-t08 | 76 | table overlap 1.000, negative overlap 0.000 |
| FP | p076-t09 | 76 | table overlap 1.000, negative overlap 0.000 |
| FP | p003-t01 | 3 | table overlap 0.000, negative overlap 1.000 |
| FP | p003-t02 | 3 | table overlap 0.000, negative overlap 1.000 |
| FP | p003-t03 | 3 | table overlap 0.000, negative overlap 1.000 |
| FP | p003-t04 | 3 | table overlap 0.000, negative overlap 1.000 |
| FP | p003-t05 | 3 | table overlap 0.000, negative overlap 1.000 |
| FP | p003-t06 | 3 | table overlap 0.000, negative overlap 1.000 |
| FP | p003-t07 | 3 | table overlap 0.000, negative overlap 1.000 |
| FP | p004-t01 | 4 | table overlap 1.000, negative overlap 0.000 |
| FP | p004-t02 | 4 | table overlap 1.000, negative overlap 0.000 |
| FP | p004-t03 | 4 | table overlap 1.000, negative overlap 0.000 |
| FP | p004-t04 | 4 | table overlap 1.000, negative overlap 0.000 |
| FP | p004-t05 | 4 | table overlap 1.000, negative overlap 0.000 |
| FP | p004-t06 | 4 | table overlap 1.000, negative overlap 0.000 |
| FP | p004-t07 | 4 | table overlap 1.000, negative overlap 0.000 |
| FP | p004-t08 | 4 | table overlap 1.000, negative overlap 0.000 |
| FP | p004-t09 | 4 | table overlap 1.000, negative overlap 0.000 |
| FP | p004-t10 | 4 | table overlap 1.000, negative overlap 0.000 |
| FP | p004-t11 | 4 | table overlap 1.000, negative overlap 0.000 |
| FP | p004-t12 | 4 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t01 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t02 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t03 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t04 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t05 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t06 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t07 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t08 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t09 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t10 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t11 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t12 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p005-t13 | 5 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t01 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t02 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t03 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t04 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t05 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t06 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t07 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t08 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t09 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t10 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t11 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t12 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t13 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t14 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t15 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t16 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t17 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t18 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p006-t19 | 6 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t01 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t02 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t03 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t04 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t05 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t06 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t07 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t08 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t09 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t10 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t11 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t12 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t13 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t14 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t15 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t16 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t17 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p008-t18 | 8 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t01 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t02 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t03 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t04 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t05 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t06 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t07 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t08 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t09 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t10 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t11 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t12 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t13 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t14 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t15 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t16 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t17 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t18 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t19 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t20 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t21 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t22 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t23 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t24 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p010-t25 | 10 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t01 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t02 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t03 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t04 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t05 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t06 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t07 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t08 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t09 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t10 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t11 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t12 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t13 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t14 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t15 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t16 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t17 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p011-t18 | 11 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t01 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t02 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t03 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t04 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t05 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t06 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t07 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t08 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t09 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t10 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t11 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t12 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t13 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t14 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t15 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t16 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t17 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t18 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t19 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t20 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t21 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t22 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t23 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p012-t24 | 12 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t01 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t02 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t03 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t04 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t05 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t06 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t07 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t08 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t09 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t10 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t11 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t12 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t13 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t14 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t15 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t16 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t17 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t18 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t19 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t20 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t21 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t22 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t23 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t24 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p014-t25 | 14 | table overlap 1.000, negative overlap 0.000 |
| FP | p015-t01 | 15 | table overlap 0.000, negative overlap 1.000 |
| FP | p015-t02 | 15 | table overlap 0.000, negative overlap 1.000 |
| FP | p015-t03 | 15 | table overlap 0.000, negative overlap 0.716 |
| FP | p033-t01 | 33 | table overlap 1.000, negative overlap 0.000 |
| FP | p033-t02 | 33 | table overlap 1.000, negative overlap 0.000 |
| FP | p033-t03 | 33 | table overlap 1.000, negative overlap 0.000 |
| FP | p033-t04 | 33 | table overlap 1.000, negative overlap 0.000 |
| FP | p033-t05 | 33 | table overlap 1.000, negative overlap 0.000 |
| FP | p033-t06 | 33 | table overlap 1.000, negative overlap 0.000 |
| FP | p033-t07 | 33 | table overlap 1.000, negative overlap 0.000 |
| FP | p033-t08 | 33 | table overlap 1.000, negative overlap 0.000 |
| FP | p033-t09 | 33 | table overlap 1.000, negative overlap 0.000 |
| FP | p033-t10 | 33 | table overlap 1.000, negative overlap 0.000 |
| FP | p033-t11 | 33 | table overlap 1.000, negative overlap 0.000 |
| FP | p033-t12 | 33 | table overlap 1.000, negative overlap 0.000 |
| FP | p033-t13 | 33 | table overlap 0.666, negative overlap 0.000 |
| rows | ADC12DJ5200-P41-T01 | 41 | gold 6 -> pred 7 |
| rows | ADC12DJ5200-P47-T01 | 47 | gold 2 -> pred 4 |
| rows | ADC12DJ5200-P78-T02 | 78 | gold 10 -> pred 8 |
| rows | ADC12DJ5200-P78-T03 | 78 | gold 18 -> pred 16 |
| rows | ADC12DJ5200-P78-T04 | 78 | gold 7 -> pred 5 |
| rows | ADC12DJ5200-P102-T03 | 102 | gold 3 -> pred 2 |
| rows | ADS1299-P17-T01 | 17 | gold 10 -> pred 9 |
| rows | ADS1299-P17-T02 | 17 | gold 10 -> pred 9 |
| rows | ADS1299-P17-T03 | 17 | gold 10 -> pred 9 |
| rows | ADS1299-P35-T01 | 35 | gold 8 -> pred 9 |
| rows | ADS1299-P37-T01 | 37 | gold 3 -> pred 2 |
| cols | ADC12DJ5200-P78-T02 | 78 | gold 17 -> pred 7 (header rows 2 -> 0) |
| cols | ADC12DJ5200-P78-T03 | 78 | gold 17 -> pred 7 (header rows 2 -> 0) |
| cols | ADC12DJ5200-P78-T04 | 78 | gold 17 -> pred 7 (header rows 2 -> 0) |
| cols | ADS1299-P37-T01 | 37 | gold 3 -> pred 4 (header rows 1 -> 0) |
| roles | ADC12DJ5200-P41-T01 | 41 | gold ['value', 'value', 'value', 'value'] -> pred ['unknown', 'unknown', 'unknown', 'unknown'] |
| roles | ADC12DJ5200-P43-T01 | 43 | gold ['symbol', 'value', 'value'] -> pred ['unknown', 'unknown', 'unknown'] |
| roles | ADC12DJ5200-P46-T01 | 46 | gold ['value', 'value', 'value', 'value'] -> pred ['unknown', 'unknown', 'unknown', 'unknown'] |
| roles | ADC12DJ5200-P47-T01 | 47 | gold ['symbol', 'value', 'value', 'value', 'value', 'value'] -> pred ['unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown'] |
| roles | ADC12DJ5200-P54-T01 | 54 | gold ['condition', 'value'] -> pred ['unknown', 'unknown'] |
| roles | ADC12DJ5200-P78-T02 | 78 | gold ['symbol', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value'] -> pred ['unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown'] |
| roles | ADC12DJ5200-P78-T03 | 78 | gold ['symbol', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value'] -> pred ['unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown'] |
| roles | ADC12DJ5200-P78-T04 | 78 | gold ['symbol', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value'] -> pred ['unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown'] |
| roles | ADC12DJ5200-P98-T01 | 98 | gold ['value', 'symbol', 'value', 'value'] -> pred ['unknown', 'unknown', 'unknown', 'unknown'] |
| roles | ADC12DJ5200-P102-T03 | 102 | gold ['value', 'value', 'value', 'value', 'value'] -> pred ['value', 'value', 'typ', 'value', 'value'] |
| roles | ADS1299-P17-T01 | 17 | gold ['symbol', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value'] -> pred ['unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown'] |
| roles | ADS1299-P17-T02 | 17 | gold ['symbol', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value', 'value'] -> pred ['unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown'] |
| roles | ADS1299-P17-T03 | 17 | gold ['symbol', 'value', 'value', 'value', 'value', 'value', 'value', 'value'] -> pred ['unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown', 'unknown'] |
| roles | ADS1299-P23-T01 | 23 | gold ['symbol', 'value'] -> pred ['unknown', 'unknown'] |
| roles | ADS1299-P35-T01 | 35 | gold ['symbol', 'value', 'unit'] -> pred ['unknown', 'unknown', 'unknown'] |
| roles | ADS1299-P37-T01 | 37 | gold ['symbol', 'min', 'unit'] -> pred ['min', 'unit', 'unknown', 'unknown'] |

## Single-row gold tables (must not be dropped)

- Gold single-row tables: 2
- Matched: 1

| Item | Matched | Prediction | Status |
| --- | --- | --- | --- |
| ADC12DJ5200-P01-T01 | False | - | - |
| ADC12DJ5200-P47-T01 | True | p047-t01 | partial |

## Cross-page tables

- Gold fragments: 4
- Matched: 2

## Negative samples

| Kind | Items | Items with FP | FP predictions |
| --- | --- | --- | --- |
| bit_field_diagram | 2 | 2 | 4 |
| chart_annotations | 3 | 3 | 27 |
| legal_notice | 2 | 0 | 0 |
| pin_diagram | 3 | 2 | 16 |
| prose | 4 | 3 | 8 |
| revision_history | 1 | 0 | 0 |
| timing_diagram | 1 | 1 | 1 |
| toc | 3 | 2 | 3 |
| **total** | **19** | **13** | **59** |

## Missed gold tables (FN)

| Item | Page | Gold rows x cols | Best IoU |
| --- | --- | --- | --- |
| ADC12DJ5200-P01-T01 | 1 | 2 x 3 | 0.0484 |
| ADC12DJ5200-P39-T01 | 39 | 8 x 7 | 0.3392 |
| ADC12DJ5200-P61-T01 | 61 | 6 x 5 | 0.0000 |
| ADC12DJ5200-P61-T02 | 61 | 14 x 4 | 0.1052 |
| ADC12DJ5200-P72-T01 | 72 | 8 x 4 | 0.0000 |
| ADC12DJ5200-P78-T01 | 78 | 7 x 3 | 0.2760 |
| ADC12DJ5200-P79-T01 | 79 | 5 x 17 | 0.4884 |
| ADC12DJ5200-P100-T01 | 100 | 38 x 4 | 0.2682 |
| ADC12DJ5200-P102-T01 | 102 | 6 x 5 | 0.1387 |
| ADC12DJ5200-P102-T02 | 102 | 3 x 5 | 0.2023 |
| ADS1299-P27-T01 | 27 | 4 x 4 | 0.3978 |
| ADS1299-P40-T01 | 40 | 14 x 4 | 0.2494 |
| ADS1299-P44-T01 | 44 | 31 x 11 | 0.2003 |
| ADS1299-P45-T01 | 45 | 5 x 5 | 0.0338 |
| ADS1299-P52-T01 | 52 | 9 x 5 | 0.0133 |
| ADS1299-P67-T01 | 67 | 5 x 2 | 0.4559 |
| ADS1299-P70-T01 | 70 | 3 x 5 | 0.3632 |
| ADS1299-P74-T01 | 74 | 4 x 6 | 0.4994 |
| ADS1299-P76-T01 | 76 | 15 x 10 | 0.1709 |
| LM358-P04-T01 | 4 | 17 x 6 | 0.1437 |
| LM358-P04-T02 | 4 | 7 x 4 | 0.2333 |
| LM358-P05-T01 | 5 | 10 x 5 | 0.2391 |
| LM358-P05-T02 | 5 | 9 x 10 | 0.1383 |
| LM358-P06-T01 | 6 | 51 x 7 | 0.0894 |
| LM358-P08-T01 | 8 | 52 x 7 | 0.0877 |
| LM358-P10-T01 | 10 | 50 x 6 | 0.0891 |
| LM358-P11-T01 | 11 | 46 x 6 | 0.1329 |
| LM358-P12-T01 | 12 | 47 x 6 | 0.0546 |
| LM358-P14-T01 | 14 | 50 x 6 | 0.0507 |
| LM358-P33-T01 | 33 | 16 x 10 | 0.0886 |

## Matched but structurally wrong

| Item | IoU | Gold rows x cols | Pred rows x cols | Row/col exact | Type | Status |
| --- | --- | --- | --- | --- | --- | --- |
| ADC12DJ5200-P41-T01 | 0.8933 | 6 x 4 | 7 x 4 | False/True | other -> unknown | partial |
| ADC12DJ5200-P47-T01 | 0.7516 | 2 x 6 | 4 x 6 | False/True | other -> unknown | partial |
| ADC12DJ5200-P78-T02 | 0.7160 | 10 x 17 | 8 x 7 | False/False | other -> unknown | reconstructed |
| ADC12DJ5200-P78-T03 | 0.8106 | 18 x 17 | 16 x 7 | False/False | other -> unknown | reconstructed |
| ADC12DJ5200-P78-T04 | 0.6159 | 7 x 17 | 5 x 7 | False/False | other -> unknown | reconstructed |
| ADC12DJ5200-P102-T03 | 0.5022 | 3 x 5 | 2 x 5 | False/True | other -> unknown | partial |
| ADS1299-P17-T01 | 0.6920 | 10 x 13 | 9 x 13 | False/True | electrical_characteristics -> unknown | reconstructed |
| ADS1299-P17-T02 | 0.6920 | 10 x 13 | 9 x 13 | False/True | electrical_characteristics -> unknown | reconstructed |
| ADS1299-P17-T03 | 0.6959 | 10 x 8 | 9 x 8 | False/True | electrical_characteristics -> unknown | reconstructed |
| ADS1299-P35-T01 | 0.6863 | 8 x 3 | 9 x 3 | False/True | electrical_characteristics -> unknown | partial |
| ADS1299-P37-T01 | 0.5220 | 3 x 3 | 2 x 4 | False/False | electrical_characteristics -> unknown | partial |

