# Gold Set evaluation: after-5layer-v4

- Gold annotation: `gold-2026-11-05.1`
- Baseline: `phase1.1-baseline` at `1d8c7220601db734b63437abd41c36739a42aa89`
- Generated: 2026-11-05T14:11:49+00:00
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
| adc12dj5200 | `20261105T141031Z-1d7e93` | `ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c` |
| ads1299 | `20261105T141010Z-9985ab` | `ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c` |
| lm358 | `20261105T140950Z-9aefb4` | `ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c` |

## Overall table detection

| Gold tables | TP | FP | FN | Precision | Recall | F1 | Out-of-scope predictions | Predictions on gold pages |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 45 | 39 | 4 | 6 | 0.9070 | 0.8667 | 0.8864 | 7 | 50 |

## Per PDF

| PDF | Gold | TP | FP | FN | Precision | Recall | F1 | Out-of-scope | Predictions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adc12dj5200 | 19 | 14 | 3 | 5 | 0.8235 | 0.7368 | 0.7778 | 3 | 20 |
| ads1299 | 15 | 14 | 0 | 1 | 1.0000 | 0.9333 | 0.9655 | 1 | 15 |
| lm358 | 11 | 11 | 1 | 0 | 0.9167 | 1.0000 | 0.9565 | 3 | 15 |

## Over-detection / fragmentation

- Predictions on gold pages: 50
- In-scope false positives: 4
- Out-of-scope predictions (unannotated page area): 7
- Mean predictions overlapping one gold table: 0.867
- Maximum predictions overlapping one gold table: 1 (ADC12DJ5200-P39-T01, ADC12DJ5200-P41-T01, ADC12DJ5200-P46-T01, ADC12DJ5200-P47-T01, ADC12DJ5200-P54-T01, ADC12DJ5200-P61-T01, ADC12DJ5200-P72-T01, ADC12DJ5200-P78-T01, ADC12DJ5200-P78-T02, ADC12DJ5200-P98-T01)
- Overlap-count distribution: {'0': 6, '1': 39}

## Structure on matched tables

| Metric | Value |
| --- | --- |
| Matched tables | 39 |
| Row count exact | 38 |
| Column count exact | 34 |
| Row and column exact | 33 |
| Cell-text F1 | 0.8302 |
| Header column accuracy | 0.5932 |
| Header tables exact | 20 |
| Column-role accuracy | 0.6398 |
| Column-role tables exact | 12 |
| Table-type accuracy | 0.5128 |
| Reconstruction status (matched) | {'reconstructed': 19, 'partial': 20} |
| Row error distribution | {'0': 38, '3': 1} |
| Column error distribution | {'-4': 1, '-2': 1, '-1': 2, '0': 34, '1': 1} |

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
| bit_field_diagram | 2 | 0 | 0 |
| chart_annotations | 3 | 0 | 0 |
| legal_notice | 2 | 0 | 0 |
| pin_diagram | 3 | 0 | 0 |
| prose | 4 | 1 | 1 |
| revision_history | 1 | 0 | 0 |
| timing_diagram | 1 | 0 | 0 |
| toc | 3 | 2 | 3 |
| **total** | **19** | **3** | **4** |

## Missed gold tables (FN)

| Item | Page | Gold rows x cols | Best IoU |
| --- | --- | --- | --- |
| ADC12DJ5200-P43-T01 | 43 | 3 x 3 | 0.0000 |
| ADC12DJ5200-P61-T02 | 61 | 14 x 4 | 0.0000 |
| ADC12DJ5200-P78-T03 | 78 | 18 x 17 | 0.0000 |
| ADC12DJ5200-P78-T04 | 78 | 7 x 17 | 0.0000 |
| ADC12DJ5200-P79-T01 | 79 | 5 x 17 | 0.0000 |
| ADS1299-P74-T01 | 74 | 4 x 6 | 0.0000 |

## Matched but structurally wrong

| Item | IoU | Gold rows x cols | Pred rows x cols | Row/col exact | Type | Status |
| --- | --- | --- | --- | --- | --- | --- |
| ADC12DJ5200-P47-T01 | 0.9979 | 2 x 6 | 5 x 6 | False/True | other -> unknown | partial |
| ADS1299-P70-T01 | 1.0000 | 3 x 5 | 3 x 4 | True/False | electrical_characteristics -> electrical_characteristics | reconstructed |
| ADS1299-P76-T01 | 1.0000 | 15 x 10 | 15 x 8 | True/False | ordering_information -> ordering_information | reconstructed |
| LM358-P04-T01 | 1.0000 | 17 x 6 | 17 x 5 | True/False | absolute_maximum -> other | partial |
| LM358-P11-T01 | 1.0000 | 46 x 6 | 46 x 7 | True/False | electrical_characteristics -> other | partial |
| LM358-P33-T01 | 1.0000 | 16 x 10 | 16 x 6 | True/False | ordering_information -> ordering_information | partial |

