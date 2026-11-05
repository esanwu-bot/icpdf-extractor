# Phase 1.3 cross-PDF generalization

Scope: test whether the frozen Phase 1.2 parser generalizes to vendor documents
that did not participate in any rule tuning.  No parser threshold, keyword or
heuristic was changed for this round; Phase 2 (LLM) stays frozen.

Status: the gold set is now `gen-2026-11-06.2`, independently reviewed against
the PDFs (see §2).  The numbers in §3 are **internal evaluation results**, not
an acceptance version: the reviewer's generalization gate remains open until
the structure redesign is reviewed.

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
`gen-2026-11-06.2`: **21 tables, 8 negatives**.  Every item was inspected on a
standalone crop rendered from the original PDF with no parser overlay; the
parser output was consulted only afterwards.  Full record:
`gold/generalization/review_record.md`.

| PDF | Tables | Negatives |
| --- | --- | --- |
| MICRF103 | 3 | 2 |
| DS10CP152 | 12 | 3 |
| CY29FCT520 | 6 | 3 |

Changes from `.1`:

* **CY29FCT520-P10-T01** added: the PINS \*\* / DIM table inside the package
  drawing is a real table; it was previously inside a negative.
* **DS10CP152-P13-T02** added: headerless 5x2 dimension-description table under
  TAPE DIMENSIONS.  Its borders are quadrilateral outlines (`qu`), which the
  parser and the rule lattice both ignore.
* **DS10CP152-N03-P13** shrunk to the drawing; the table is no longer inside a
  negative.
* All negatives re-derived from the rendered page.  In v1, five of eight
  negative boxes reproduced a parser prediction exactly and three reproduced a
  rule component — provenance leakage that made negative hits partly
  self-fulfilling.
* DS10CP152-N01 reclassified `layout` → `prose`; CY29FCT520-N01 reclassified
  `drawing` → `pin_diagram`.
* CY29FCT520-P06-T01 header corrected: the PDF overprints the same UNIT word
  twice at identical coordinates; the lattice had concatenated `UNIT UNIT`.

Gold Spec v2 conventions (`docs/GOLD_SPEC.md`):

* Every table records `visual_columns` and its `visual_boundary_status`
  (`printed` / `partial` / `implied_outer` / `not_printed`) separately from
  `logical_columns`.  The four column metrics use different denominators and
  exclusions.
* MICRF103-P03-T01 is one logical electrical-characteristics table: five rule
  components are merged, section-title bands become full-width body rows, and
  the outer Symbol/Units columns (delimited only by the horizontal rules) are
  explicit boundaries (`implied_outer`).
* Unlabeled columns stay `unknown` (DS10CP152-P03-T02 first column,
  CY29FCT520-P04-T01 left band, CY29FCT520-P06-T01 first two header cells).
* Header canopy labels are attached to all covered columns through explicit
  header merges, so `MIN/NOM/MAX` columns carry the device-group label.
* Headerless tables keep `header_rows: 0` (DS10CP152-P03-T01,
  DS10CP152-P13-T02).
* A negative may contain a positive table island (CY29FCT520-N03-P10 contains
  CY29FCT520-P10-T01).

## 3. Results (frozen parser, internal)

Overall: **TP 19 / FP 7 / FN 2**, precision 0.7308, recall 0.9048, F1 0.8085;
4 negative-sample false positives across 4 of 8 negatives; 7 out-of-scope
predictions.

| PDF | Gold | TP | In-scope FP | FN | Precision | Recall |
| --- | --- | --- | --- | --- | --- | --- |
| MICRF103 | 3 | 2 | 4 | 1 | 0.3333 | 0.6667 |
| DS10CP152 | 12 | 11 | 1 | 1 | 0.9167 | 0.9167 |
| CY29FCT520 | 6 | 6 | 2 | 0 | 0.7500 | 1.0000 |

Structure on the 19 matched tables:

| Metric | Value | Denominator |
| --- | --- | --- |
| Row count exact | 19 / 19 | matched tables |
| Visual boundary exact | 11 / 17 | matched tables with printed, partial or implied visual boundaries; 2 `not_printed` excluded |
| Logical column exact | 16 / 19 | matched tables with a decided logical mapping; 0 undecided |
| Row and column exact | 16 / 19 | matched tables |
| Cell-text F1 | 0.8443 | matched tables |
| Header column accuracy (compact) | 1.0000 | 95 labelled columns / 16 comparable tables |
| Header column accuracy (strict spacing) | 1.0000 | same |
| Header row-depth exact | 18 / 19 | matched tables |
| Header cell-text F1 | 0.9896 | 16 comparable tables |
| Multi-layer header exact | 4 / 4 | header_rows >= 2 |
| Column-role accuracy | 0.8586 | 99 columns in comparable matched tables |
| Table-type accuracy | 0.6316 | matched tables |

Column-role by role: `typ` 7/7, `unit` 5/5, `min` 5/7, `max` 5/7,
`condition` 3/9, `symbol` 11/13, `value` 49/49, `unknown` 0/2.

## 4. Error analysis

### 4.1 Detection: two false negatives

* **MICRF103-P03-T01** (best IoU 0.2335).  On page 3 the table's left Symbol
  and right Units columns lie outside every vertical rule; the rule lattice
  bbox is `184.1-554.9`, while the printed table spans `46.8-586.8`.  The parser
  builds three fragment tables (`p003-t01..t03`) inside the gold region, all
  scored as in-scope false positives, and never emits the Reference Oscillator
  section.  This is the outer-boundary and fragmentation family.
* **DS10CP152-P13-T02** (IoU 0.0).  The table is fully ruled, but each cell is
  an axis-aligned quadrilateral outline.  The parser reads lines and thin
  rects only, so it never sees the ruling; the frozen run has no prediction on
  that part of page 13.  This is a genuine unseen-construct failure.

### 4.2 Detection: negatives

Four negative false positives, one each:

| Negative | Kind | Parser output | Overlap |
| --- | --- | --- | --- |
| CY29FCT520-N02-P02 | schematic | `p002-t01` | 0.921 |
| CY29FCT520-N03-P10 | drawing | `p010-t01` | 1.000 |
| DS10CP152-N01-P01 | prose | `p001-t01` | 1.000 |
| MICRF103-N02-P04 | schematic | `p004-t01` | 1.000 |

The pinout negative (CY29FCT520-N01) no longer produces a hit after being
re-drawn from the page; the old hit was partly an artefact of the negative
being the parser box.  Drawings and schematics remain the dominant
false-positive source on unseen vendors.

### 4.3 Columns: sub-rules vs logical columns

Three logical column-count mismatches:

* CY29FCT520-P05-T01: gold 9, parser 11.  Test-condition sub-rules
  (`193.9`, `266.0`) and device-group sub-rules are promoted to columns.
* CY29FCT520-P06-T01: gold 7, parser 6.  The unlabeled left band and the
  Data/I condition band are collapsed.
* CY29FCT520-P08-T01: gold 12, parser 9.  The packaging table has no vertical
  rules at all, so projection misses three adjacent narrow columns.

Visual boundary exactness is 11/17.  The six misses are the tables where the
parser's count is the logical count instead of the printed count:
CY29FCT520-P04-T01 (4 visual / 8 logical), P04-T02 (6/9), P05 (7/9), P06 (5/7),
DS10CP152-P04 (8/7) and P05 (8/7).  This is exactly the distinction Gold Spec
v2 introduced: partial condition sub-rules are visible boundaries but not
automatically logical columns.

### 4.4 Headers and roles

Header attribution is exact on every comparable table (95/95 columns, compact
and strict).  The only row-depth miss is DS10CP152-P03-T01: a headerless
two-column list gets an invented header because the first row is bold.

Role accuracy 0.8586.  Main causes:

* the two gold `unknown` columns are both predicted as `symbol` (the
  `_leading_role` heuristic guesses a symbol for an unlabeled leading column);
* six gold `condition` columns are lost because the parser splits or merges
  those columns (CY29FCT520-P04/P05/P06);
* `min`/`max` recall 0.7143 (2 each) follows from the same column splits.

These are exactly the cases the evidence layer exposes: a role derived from a
header cell can be cited, the unlabeled leading column cannot, and it should
stay `unknown`.

## 5. What this round proves — and does not

Proves:

* the gold itself was independently checked PDF-first for all 21 tables and 8
  negatives, with corrections recorded in `review_record.md`;
* the evidence chain (Candidate → Table/Row/Cell/HeaderPath/HeaderCell, role
  provenance) holds on three unseen vendors, 33 tables and 1,201 candidates,
  with zero validation errors;
* row segmentation and header attribution generalize: 19/19 row counts,
  95/95 header columns, 4/4 multi-layer headers;
* the Phase 1.2 metrics still reproduce exactly after the evidence changes
  (46/46 detection, 46 row, 44 column, 0.9897 role).

Does not prove:

* precision on unseen vendors — 4 negative FPs, one fragmented table and one
  invisible (quad-ruled) table show drawings and rule-poor tables are not
  solved;
* column-count generalization for tables without internal vertical rules, or
  the visual/logical separation the parser does not yet emit;
* anything about scanned PDFs (all three documents have a text layer);
* Phase 2 readiness.  These results are Phase 1.3 evidence only; the
  generalization gate stays open and this report is not an acceptance version.

## 6. Reproduce

```bash
export PYTHONPATH=src:. PYTHONIOENCODING=utf-8
python -m icpdf.cli parse --pdf "<MICRF103 path>" --mpn MICRF103YM --runs runs/phase13_generalization
python -m tools.validate_evidence --run runs/phase13_generalization/<run> --strict
python -m tools.goldset.annotate --spec gold/generalization/spec.yaml --out-dir gold/generalization
python -m tools.goldset.render_review_crops --spec gold/generalization/spec.yaml --out-dir gold/generalization/review_crops
python -m tools.goldset.evaluate \
  --gold gold/generalization/gold_table_set.jsonl \
  --run runs/phase13_generalization/20261105T184617Z-18afbb \
  --run runs/phase13_generalization/20261105T184625Z-8e26e5 \
  --run runs/phase13_generalization/20261105T184633Z-749c5a \
  --label gen-2026-11-06.2-internal \
  --out runs/phase13_generalization/eval_v2_internal.md \
  --json runs/phase13_generalization/eval_v2_internal.json \
  --csv runs/phase13_generalization/eval_v2_internal.csv
```
