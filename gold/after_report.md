# Gold Set evaluation: after-5layer-v5

- Gold annotation: `gold-2026-11-06.1`
- Baseline: `phase1.1-baseline` at `1d8c7220601db734b63437abd41c36739a42aa89`
- Generated: 2026-11-05T18:18:11+00:00
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
| adc12dj5200 | `20261105T181640Z-359a61` | `ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c` |
| ads1299 | `20261105T181637Z-932cfb` | `ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c` |
| lm358 | `20261105T181633Z-610c7a` | `ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c` |

## Overall table detection

| Gold tables | TP | FP | FN | Precision | Recall | F1 | Out-of-scope predictions | Predictions on gold pages |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 46 | 46 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 8 | 54 |

## Per PDF

| PDF | Gold | TP | FP | FN | Precision | Recall | F1 | Out-of-scope | Predictions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adc12dj5200 | 20 | 20 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 3 | 23 |
| ads1299 | 15 | 15 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 2 | 17 |
| lm358 | 11 | 11 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | 3 | 14 |

## Over-detection / fragmentation

- Predictions on gold pages: 54
- In-scope false positives: 0
- Out-of-scope predictions (unannotated page area): 8
- Mean predictions overlapping one gold table: 1.0
- Maximum predictions overlapping one gold table: 1 (ADC12DJ5200-P01-T01, ADC12DJ5200-P39-T01, ADC12DJ5200-P41-T01, ADC12DJ5200-P43-T01, ADC12DJ5200-P46-T01, ADC12DJ5200-P47-T01, ADC12DJ5200-P54-T01, ADC12DJ5200-P61-T01, ADC12DJ5200-P61-T02, ADC12DJ5200-P72-T01)
- Overlap-count distribution: {'1': 46}

## Structure on matched tables

| Metric | Value |
| --- | --- |
| Matched tables | 46 |
| Row count exact | 46 |
| Column count exact | 44 |
| Row and column exact | 44 |
| Cell-text F1 | 0.8889 |
| Header column accuracy | 1.0000 |
| Header column accuracy (strict spacing) | 0.9582 |
| Header row-depth exact | 46 | (of 46 matched) |
| Header tables exact | 44 | (of 44 comparable) |
| Header cell-text F1 | 1.0000 |
| Multi-layer header exact | 10 | (of 10) |
| Tables carrying header_path | 46 |
| Column-role accuracy | 0.9897 |
| Column-role tables exact | 41 |
| Table-type accuracy | 0.5870 |
| Reconstruction status (matched) | {'reconstructed': 30, 'partial': 16} |
| Row error distribution | {'0': 46} |
| Column error distribution | {'-1': 2, '0': 44} |

## Metric denominators

| Metric family | Denominator |
| --- | --- |
| detection_precision | TP + in-scope FP (predictions on annotated pages) |
| detection_recall | TP + FN (accepted gold tables) |
| row_count | 46 matched tables |
| column_count | 46 matched tables |
| cell_text | matched tables; multiset F1 over non-empty cell texts |
| header_cell_text | 44 matched tables with equal column count; multiset F1 over non-empty header labels, whitespace-free |
| header_column_attribution | 287 labelled gold header columns (empty gold labels excluded) in 44 comparable matched tables; strict variant keeps intra-label spacing |
| header_multilayer | 10 matched gold tables with header_rows >= 2 |
| header_row_detection | header_rows exact over all matched tables |
| column_role | 292 gold columns in comparable matched tables |

## Column roles by role

| Role | Gold columns | Predicted columns | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| min | 8 | 8 | 8 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| typ | 6 | 6 | 6 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| max | 7 | 7 | 7 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| unit | 11 | 11 | 11 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 |
| condition | 22 | 20 | 20 | 0 | 2 | 1.0000 | 0.9091 | 0.9524 |
| symbol | 32 | 33 | 32 | 1 | 0 | 0.9697 | 1.0000 | 0.9846 |
| value | 206 | 206 | 205 | 1 | 1 | 0.9951 | 0.9951 | 0.9951 |
| unknown | 0 | 1 | 0 | 1 | 0 | 0.0000 | 0.0000 | 0.0000 |

## Confusion matrices

### table_type

| gold \ pred | absolute_maximum | recommended_operating | electrical_characteristics | thermal | pin_functions | ordering_information | other | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| absolute_maximum | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| recommended_operating | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| electrical_characteristics | 0 | 0 | 2 | 0 | 0 | 0 | 13 | 0 |
| thermal | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| pin_functions | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| ordering_information | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 0 |
| other | 0 | 0 | 0 | 0 | 0 | 0 | 22 | 0 |
| unknown | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### header_rows

| gold \ pred | 0 | 1 | 2 | 3 | 4 |
| --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 0 | 36 | 0 | 0 | 0 |
| 2 | 0 | 0 | 9 | 0 | 0 |
| 3 | 0 | 0 | 0 | 1 | 0 |
| 4 | 0 | 0 | 0 | 0 | 0 |

### column_role

| gold \ pred | min | typ | max | unit | condition | symbol | value | unknown |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| min | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| typ | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 |
| max | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 0 |
| unit | 0 | 0 | 0 | 11 | 0 | 0 | 0 | 0 |
| condition | 0 | 0 | 0 | 0 | 20 | 0 | 1 | 1 |
| symbol | 0 | 0 | 0 | 0 | 0 | 32 | 0 | 0 |
| value | 0 | 0 | 0 | 0 | 0 | 1 | 205 | 0 |
| unknown | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Error cases

- Missed tables (FN): 0
- In-scope false positives: 0
- Row-count mismatches: 0
- Column-count mismatches: 2
- Header-text mismatches: 0
- Column-role mismatches: 5

| Case | Item | Page | Detail |
| --- | --- | --- | --- |
| cols | ADS1299-P70-T01 | 70 | gold 5 -> pred 4 (header rows 1 -> 1) |
| cols | LM358-P04-T01 | 4 | gold 6 -> pred 5 (header rows 1 -> 1) |
| roles | ADC12DJ5200-P46-T01 | 46 | gold ['value', 'value', 'value', 'value'] -> pred ['symbol', 'value', 'value', 'value'] |
| roles | ADS1299-P27-T01 | 27 | gold ['symbol', 'condition', 'condition', 'value'] -> pred ['symbol', 'value', 'condition', 'value'] |
| roles | ADS1299-P70-T01 | 70 | gold ['symbol', 'value', 'min', 'max', 'unit'] -> pred ['symbol', 'min', 'max', 'unit'] |
| roles | LM358-P04-T01 | 4 | gold ['symbol', 'condition', 'condition', 'min', 'max', 'unit'] -> pred ['symbol', 'condition', 'min', 'max', 'unit'] |
| roles | LM358-P04-T02 | 4 | gold ['symbol', 'condition', 'value', 'unit'] -> pred ['symbol', 'unknown', 'value', 'unit'] |

## Single-row gold tables (must not be dropped)

- Gold single-row tables: 2
- Matched: 2

| Item | Matched | Prediction | Status |
| --- | --- | --- | --- |
| ADC12DJ5200-P01-T01 | True | p001-t01 | reconstructed |
| ADC12DJ5200-P47-T01 | True | p047-t01 | reconstructed |

## Cross-page tables

- Gold fragments: 4
- Matched: 4

## Negative samples

| Kind | Items | Items with FP | FP predictions |
| --- | --- | --- | --- |
| bit_field_diagram | 2 | 0 | 0 |
| chart_annotations | 3 | 0 | 0 |
| legal_notice | 2 | 0 | 0 |
| pin_diagram | 3 | 0 | 0 |
| prose | 4 | 0 | 0 |
| revision_history | 1 | 0 | 0 |
| timing_diagram | 1 | 0 | 0 |
| toc | 3 | 0 | 0 |
| **total** | **19** | **0** | **0** |

## Missed gold tables (FN)

| Item | Page | Gold rows x cols | Best IoU |
| --- | --- | --- | --- |

## Matched but structurally wrong

| Item | IoU | Gold rows x cols | Pred rows x cols | Row/col exact | Type | Status |
| --- | --- | --- | --- | --- | --- | --- |
| ADS1299-P70-T01 | 1.0000 | 3 x 5 | 3 x 4 | True/False | electrical_characteristics -> electrical_characteristics | reconstructed |
| LM358-P04-T01 | 1.0000 | 17 x 6 | 17 x 5 | True/False | absolute_maximum -> other | partial |

