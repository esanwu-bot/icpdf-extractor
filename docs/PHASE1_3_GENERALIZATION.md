# Phase 1.3 cross-PDF generalization

Scope: test whether the frozen Phase 1.2 parser generalizes to vendor documents
that did not participate in any rule tuning.  No parser threshold, keyword or
heuristic was changed for this round; Phase 2 (LLM) stays frozen.

## 1. Freeze

`gold/generalization/PARAMS_FROZEN.json` (committed before the first run) pins:

* parser commit `f8032cce69ef94e30dda41a92286d0a62678f070`, tag `phase1.3-evidence-slice1`
* `configs/parser.yaml` SHA-256 `ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c`
* the three documents and their SHA-256

| Vendor | Document | Pages | SHA-256 (prefix) |
| --- | --- | --- | --- |
| Micrel | MICRF103 QwikRadio UHF ASK Transmitter | 7 | `670a1fab95cd` |
| National / TI | DS10CP152 1.5 Gbps 2x2 LVDS crosspoint | 17 | `14f395e46ca6` |
| Cypress / TI | CY29FCT520T multilevel pipeline register | 12 | `5f374e762b0b` |

Runs (immutable, gitignored):

| PDF | Run | Tables | Candidates |
| --- | --- | --- | --- |
| MICRF103 | `20261105T184617Z-18afbb` | 6 | 88 |
| DS10CP152 | `20261105T184625Z-8e26e5` | 13 | 523 |
| CY29FCT520 | `20261105T184633Z-749c5a` | 14 | 590 |

Evidence-chain validation (`tools/validate_evidence.py --strict`) on all three
runs: 0 errors, 0 warnings.  Header cells 6 / 77 / 124; role sources
`header_text` 33 / 468 / 494, `heuristic` 22 / 53 / 51, `fail_closed` 33 / 2 / 45.

## 2. Gold set

`gold/generalization/spec.yaml` → `gold_table_set.jsonl`, annotation version
`gen-2026-11-06.1`: **19 tables, 8 negatives**, every table checked against a
rendered page image and the generated overlay.

| PDF | Tables | Negatives |
| --- | --- | --- |
| MICRF103 | 3 | 2 |
| DS10CP152 | 11 | 3 |
| CY29FCT520 | 5 | 3 |

Conventions applied (Gold spec v2 draft, `docs/GOLD_SPEC.md`):

* MICRF103-P03-T01 is one logical electrical-characteristics table: five rule
  components are merged, section-title bands become full-width rows, and the
  outer Symbol/Units columns (delimited only by the horizontal rules) are
  explicit boundaries.
* Unlabeled columns stay `unknown` (DS10CP152-P03-T02 first column,
  CY29FCT520-P04-T01 left band, CY29FCT520-P06-T01 left band).
* Header canopy labels are attached to all covered columns through explicit
  header merges, so `MIN/NOM/MAX` columns carry the device-group label.
* Headerless DS10CP152-P03-T01 keeps `header_rows: 0`.

## 3. Results (frozen parser)

Overall: **TP 18 / FP 9 / FN 1**, precision 0.6667, recall 0.9474, F1 0.7826;
6 negative-sample false positives; 6 out-of-scope predictions.

| PDF | Gold | TP | In-scope FP | FN | Precision | Recall |
| --- | --- | --- | --- | --- | --- | --- |
| MICRF103 | 3 | 2 | 4 | 1 | 0.3333 | 0.6667 |
| DS10CP152 | 11 | 11 | 1 | 0 | 0.9167 | 1.0000 |
| CY29FCT520 | 5 | 5 | 4 | 0 | 0.5556 | 1.0000 |

Structure on the 18 matched tables:

| Metric | Value | Denominator |
| --- | --- | --- |
| Row count exact | 18 / 18 | matched tables |
| Column count exact | 15 / 18 | matched tables |
| Cell-text F1 | 0.8637 | matched tables |
| Header column accuracy (compact) | 1.0000 | 92 labelled columns / 15 comparable tables |
| Header column accuracy (strict spacing) | 1.0000 | same |
| Header row-depth exact | 17 / 18 | matched tables |
| Header cell-text F1 | 0.9892 | 15 comparable tables |
| Multi-layer header exact | 4 / 4 | header_rows >= 2 |
| Column-role accuracy | 0.8542 | 96 columns |
| Table-type accuracy | 0.6111 | matched tables |

## 4. Error analysis

### 4.1 Detection: one real structural failure

MICRF103-P03-T01 is a false negative (best IoU 0.2335).  On page 3 the table's
left Symbol and right Units columns lie outside every vertical rule; the rule
lattice bbox is `184.1-554.9`, while the printed table spans `46.8-586.8`.
The parser builds three fragment tables (`p003-t01..t03`) inside the gold
region, all scored as in-scope false positives, and never emits the Reference
Oscillator section (component at `448.1-530.0`).  So both the table boundary
and the section coverage fail.  This is a generalization gap, not a gold
convention difference: the same printed table is what Phase 1.2 gold calls one
table.

### 4.2 Detection: negatives

Six negative false positives, covering five of eight negative samples:

| Negative | Parser output | Pattern |
| --- | --- | --- |
| CY29FCT520-P01 pinout drawing | `p001-t01` | text-alignment fallback on a pinout diagram |
| CY29FCT520-P02 pipeline-instruction diagram | `p002-t01` | block diagram with boxed labels |
| CY29FCT520-P10 package drawing | `p010-t01`, `p010-t02` | dimension drawing with rules |
| DS10CP152-P01 feature/header band | `p001-t01` | two-column marketing header, no data |
| MICRF103-P04 test circuit | `p004-t01` | schematic with a rule-like box |

Drawings remain the dominant false-positive source on unseen vendors; the
Phase 1.2 gold set had no drawing negatives from these vendors.

### 4.3 Columns: sub-rules vs logical columns

Three column-count mismatches:

* CY29FCT520-P05-T01: gold 9, parser 11.  Test-condition sub-rules
  (`193.9`, `266.0`) and device-group sub-rules are promoted to columns.
* CY29FCT520-P06-T01: gold 7, parser 6.  The unlabeled left band and the
  Data/I condition band are collapsed.
* CY29FCT520-P08-T01: gold 12, parser 9.  The packaging table has no vertical
  rules at all, so projection misses three adjacent narrow columns.

The MICRF103 outer-column case (4.1) is the same family: rules inside the table
are treated as the table boundary.

### 4.4 Headers and roles

Header attribution is exact on every comparable table (92/92 columns, compact
and strict).  The only row-depth miss is DS10CP152-P03-T01: a headerless
two-column list gets an invented header because the first row is bold.

Role accuracy 0.8542 (82/96).  Main causes:

* the two gold `unknown` columns are both predicted as `symbol` (the
  `_leading_role` heuristic guesses a symbol for an unlabeled leading column);
* six gold `condition` columns are lost because the parser splits or merges
  those columns (CY29FCT520-P04/P05/P06);
* `min`/`max` recall 0.7143 (2 each) follows from the same column splits.

These are exactly the cases the evidence layer is meant to expose: a role
derived from a header cell can be cited, the unlabeled leading column cannot,
and it should stay `unknown`.

## 5. What this round proves — and does not

Proves:

* the evidence chain (Candidate → Table/Row/Cell/HeaderPath/HeaderCell,
  role provenance) holds on three unseen vendors, 33 tables and 1,201
  candidates, with zero validation errors;
* row segmentation and header attribution generalize: 18/18 row counts,
  92/92 header columns, 4/4 multi-layer headers;
* the Phase 1.2 metrics still reproduce exactly after the evidence changes
  (46/46 detection, 46 row, 44 column, 0.9897 role).

Does not prove:

* precision on unseen vendors — 6 negative FPs and one fragmented table show
  drawings and rule-poor tables are not solved;
* column-count generalization for tables without internal vertical rules;
* anything about scanned PDFs (all three documents have a text layer);
* Phase 2 readiness.  These results are Phase 1.3 evidence only, and the new
  gold has not been independently reviewed.

## 6. Reproduce

```bash
export PYTHONPATH=src:. PYTHONIOENCODING=utf-8
python -m icpdf.cli parse --pdf "<MICRF103 path>" --mpn MICRF103YM --runs runs/phase13_generalization
python -m tools.validate_evidence --run runs/phase13_generalization/<run> --strict
python -m tools.goldset.annotate --spec gold/generalization/spec.yaml --out-dir gold/generalization
python -m tools.goldset.evaluate \
  --gold gold/generalization/gold_table_set.jsonl \
  --run runs/phase13_generalization/20261105T184617Z-18afbb \
  --run runs/phase13_generalization/20261105T184625Z-8e26e5 \
  --run runs/phase13_generalization/20261105T184633Z-749c5a \
  --label gen-2026-11-06.1 --out runs/phase13_generalization/eval.md \
  --json runs/phase13_generalization/eval.json --csv runs/phase13_generalization/eval.csv
```
