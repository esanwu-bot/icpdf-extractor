# Gold Set evaluation: baseline-1d8c722

- Gold annotation: `gold-2026-11-05.1`
- Baseline: `phase1.1-baseline` at `1d8c7220601db734b63437abd41c36739a42aa89`
- Generated: 2026-11-05T13:36:58+00:00
- Matching: one-to-one per page, IoU >= 0.5; in-scope FP when overlap/prediction >= 0.25
- Scope: prediction must overlap an annotated table or negative region

## Gold set composition

| PDF | Tables | Negatives |
| --- | --- | --- |
| adc12dj5200 | 19 | 7 |
| ads1299 | 15 | 7 |
| lm358 | 11 | 5 |

Table types: {'absolute_maximum': 2, 'electrical_characteristics': 15, 'ordering_information': 2, 'other': 22, 'pin_functions': 2, 'recommended_operating': 1, 'thermal': 1}

## Runs

| PDF | Run | Parser config SHA256 |
| --- | --- | --- |
| adc12dj5200 | `20261105T124735Z-1ab90a` | `e582fa62efbef6b816095e4e7a972a88e2ed40f8c4578c8dacacb5ea43f6f98a` |
| ads1299 | `20261105T124706Z-b154f5` | `e582fa62efbef6b816095e4e7a972a88e2ed40f8c4578c8dacacb5ea43f6f98a` |
| lm358 | `20261105T124640Z-16e592` | `e582fa62efbef6b816095e4e7a972a88e2ed40f8c4578c8dacacb5ea43f6f98a` |

## Overall table detection

| Gold tables | TP | FP | FN | Precision | Recall | F1 | Out-of-scope predictions | Predictions on gold pages |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 45 | 16 | 309 | 29 | 0.0492 | 0.3556 | 0.0865 | 68 | 393 |

## Per PDF

| PDF | Gold | TP | FP | FN | Precision | Recall | F1 | Out-of-scope | Predictions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adc12dj5200 | 19 | 10 | 61 | 9 | 0.1408 | 0.5263 | 0.2222 | 10 | 81 |
| ads1299 | 15 | 6 | 71 | 9 | 0.0779 | 0.4000 | 0.1304 | 22 | 99 |
| lm358 | 11 | 0 | 177 | 11 | 0.0000 | 0.0000 | 0.0000 | 36 | 213 |

## Over-detection / fragmentation

- Predictions on gold pages: 393
- In-scope false positives: 309
- Out-of-scope predictions (unannotated page area): 68
- Mean predictions overlapping one gold table: 5.911
- Maximum predictions overlapping one gold table: 25 (LM358-P10-T01, LM358-P14-T01)
- Overlap-count distribution: {'0': 2, '1': 17, '2': 1, '3': 8, '4': 2, '5': 1, '8': 3, '9': 1, '10': 1, '12': 1, '13': 2, '18': 2, '19': 1, '24': 1, '25': 2}

## Structure on matched tables

| Metric | Value |
| --- | --- |
| Matched tables | 16 |
| Row count exact | 5 |
| Column count exact | 12 |
| Row and column exact | 5 |
| Cell-text F1 | 0.8655 |
| Header column accuracy | 0.0413 |
| Header tables exact | 1 |
| Column-role accuracy | 0.0331 |
| Column-role tables exact | 0 |
| Table-type accuracy | 0.0000 |
| Reconstruction status (matched) | {'partial': 6, 'reconstructed': 10} |
| Row error distribution | {'-2': 3, '-1': 5, '0': 5, '1': 2, '2': 1} |
| Column error distribution | {'-10': 3, '0': 12, '1': 1} |

## Single-row gold tables (must not be dropped)

- Gold single-row tables: 1
- Matched: 1

| Item | Matched | Prediction | Status |
| --- | --- | --- | --- |
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

