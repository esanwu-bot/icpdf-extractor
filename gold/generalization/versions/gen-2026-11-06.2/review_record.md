# Independent review record — `gen-2026-11-06.2`

- Reviewer: independent second pass (fresh context, PDF-first)
- Date: 2026-11-06
- Gold set: `gold/generalization/` (3 PDFs, 21 tables, 8 negatives)
- Previous version: `gen-2026-11-06.1` (frozen, immutable)
- Review status: **complete** — all 21 tables and all 8 negatives inspected

## Method

1. Standalone crops were rendered from the original PDFs with **no parser
   overlay** (`tools/goldset/render_review_crops.py` →
   `review_crops/indep_<item_id>.png`).
2. Each item was read off the rendered page first: table extent, printed
   column separators, header depth, merged spans, column roles and negative
   rejection class.
3. Gold records were compared against those observations. Parser output was
   consulted only after each PDF-first pass, and only to classify a failure as
   a detector or a gold problem. No decision was copied from a parser box.
4. Corrections were applied to `spec.yaml`, the gold set was regenerated, and
   the changed items were re-inspected.

The focus items requested by the reviewer were MICRF103-P03 and
CY29FCT520-P05/P06/P08; all four were re-derived from their crops and are
recorded below.

## Corrections in this version

| Item | Change | Why |
| --- | --- | --- |
| CY29FCT520-P10-T01 | **new positive table** | The PINS \*\* / DIM table inside the package drawing is a real 3x5 table. In v1 it was inside a negative, so a drawing hit and a table hit were indistinguishable. |
| DS10CP152-P13-T02 | **new positive table** | Headerless 5x2 dimension-description table (A0/B0/K0/W/P1) under TAPE DIMENSIONS. Its cell borders are quadrilateral outlines, which both the lattice and the parser ignore. |
| DS10CP152-N03-P13 | bbox shrunk to `[275.5, 118.0, 505.7, 208.0]` | The v1 box included the real P13-T02 table, which starts at y=213.5. |
| DS10CP152-N01-P01 | kind `layout` → `prose`; bbox `[54.0, 126.7, 558.0, 336.0]` | The v1 box was the parser's FEATURES heading box and omitted the DESCRIPTION prose. It now stops before APPLICATIONS (y=338). |
| MICRF103-N01-P01 | bbox re-drawn `[135.2, 552.0, 500.3, 720.1]` | v1 box was the rule component `140.1/564.8/395.0/699.1`. |
| MICRF103-N02-P04 | bbox re-drawn `[159.9, 193.7, 430.9, 279.2]` | v1 box equalled parser prediction `p004-t01`. |
| DS10CP152-N02-P06 | bbox re-drawn `[116.4, 106.0, 494.4, 208.4]` | v1 box was the rule component `230.8/122.3/408.0/187.0`. |
| CY29FCT520-N01-P01 | kind `drawing` → `pin_diagram`; bbox `[397.1, 74.8, 493.6, 256.6]` | v1 box equalled parser prediction `p001-t01` and covered only part of the pinout. |
| CY29FCT520-N02-P02 | bbox re-drawn `[157.3, 74.8, 437.7, 191.2]` | v1 box equalled parser prediction `p002-t01`. |
| CY29FCT520-N03-P10 | note records the positive island | The v1 bbox equalled parser prediction `p010-t01` **and** the drawing extents measured from the page (65.8/106.8/566.2/475.6), so the coordinates were retained; the contained P10 table is now a separate positive. |
| CY29FCT520-P06-T01 | header corrected to `UNIT` | The PDF overprints the same UNIT word twice at identical coordinates; the lattice had concatenated it as `UNIT UNIT`. |
| all tables | `visual_columns`, `visual_boundary_status`, `partial_boundaries`, `logical_columns` added | Gold Spec v2 split visual boundary exactness from logical column exactness. |

### Negative provenance defect

Five of the eight v1 negatives reproduced a parser prediction exactly
(MICRF103-N02, DS10CP152-N01, CY29FCT520-N01/N02/N03). The other three
reproduced a rule component from the annotation lattice (MICRF103-N01,
DS10CP152-N02, DS10CP152-N03). That leakage made negative false positives
partly self-fulfilling. All eight were checked against the rendered page in
this pass; seven were re-drawn, and CY29FCT520-N03 was retained only because
its parser box coincides exactly with the drawing extents measured directly
from the page.

## Vertical-rule and column findings

| Item | Visual | Status | Logical | Note |
| --- | --- | --- | --- | --- |
| MICRF103-P03-T01 | 6 | implied_outer | 6 | outer verticals are not printed; horizontal rules imply the sides |
| DS10CP152-P03-T01 | 2 | partial | 2 | key/value list; separator exists only in some row bands |
| DS10CP152-P04-T01 | 8 | partial | 7 | condition sub-rule at 346.1 |
| DS10CP152-P05-T01 | 8 | partial | 7 | condition sub-rule at 363.1 |
| DS10CP152-P11-T01 | — | not_printed | 10 | landscape packaging table; shaded header bands only |
| DS10CP152-P13-T02 | 2 | printed | 2 | quad-outline cells; no line/rect ruling |
| CY29FCT520-P04-T01 | 4 | printed | 8 | two-level header; blank corner is unknown |
| CY29FCT520-P04-T02 | 6 | partial | 9 | sub-rules at 173.2 |
| CY29FCT520-P05-T01 | 7 | partial | 9 | partials at 193.9 and 266.0 |
| CY29FCT520-P06-T01 | 5 | partial | 7 | partial at 289.8 |
| CY29FCT520-P08-T01 | — | not_printed | 12 | no vertical ruling; logical columns from labels |
| CY29FCT520-P10-T01 | 3 | printed | 3 | diagonal split header cell |

## Item status

| Item | Status | Key observation |
| --- | --- | --- |
| MICRF103-P01-T01 | confirmed | 3x2 ordering table; all boundaries ruled |
| MICRF103-P02-T01 | confirmed | 3x9 pin description |
| MICRF103-P03-T01 | confirmed_with_note | 6x30, section labels are full-width body rows; parser fragments it into 3 predictions |
| DS10CP152-P02-T01 | confirmed | 4x8 pin description |
| DS10CP152-P03-T01 | confirmed_with_note | headerless 2x21 absolute-maximum list |
| DS10CP152-P03-T02 | confirmed | 5x4 recommended operating; blank corner |
| DS10CP152-P04-T01 | confirmed_with_note | 7 logical / 8 visual |
| DS10CP152-P05-T01 | confirmed_with_note | 7 logical / 8 visual |
| DS10CP152-P07-T01 | confirmed | 4x5 truth table |
| DS10CP152-P07-T02 | confirmed | 4x5 truth table |
| DS10CP152-P11-T01 | confirmed_with_note | 10 columns, not printed |
| DS10CP152-P13-T01 | confirmed | 13x2 tape and reel |
| DS10CP152-P13-T02 | corrected | new headerless 5x2 dimension list |
| DS10CP152-P14-T01 | confirmed | 8x2 tube dimensions |
| DS10CP152-P15-T01 | confirmed | 9x3 reel dimensions |
| CY29FCT520-P04-T01 | confirmed_with_note | 4 visual / 8 logical, two-level header |
| CY29FCT520-P04-T02 | confirmed_with_note | 6 visual / 9 logical |
| CY29FCT520-P05-T01 | confirmed_with_note | 7 visual / 9 logical |
| CY29FCT520-P06-T01 | corrected | header duplication fixed; 5 visual / 7 logical |
| CY29FCT520-P08-T01 | confirmed_with_note | 12 logical, not printed |
| CY29FCT520-P10-T01 | corrected | new PINS/DIM table inside the drawing |
| MICRF103-N01-P01 | corrected | schematic figure re-drawn from page |
| MICRF103-N02-P04 | corrected | schematic figure re-drawn from page |
| DS10CP152-N01-P01 | corrected | prose negative; kind and extent fixed |
| DS10CP152-N02-P06 | corrected | schematic figure re-drawn from page |
| DS10CP152-N03-P13 | corrected | drawing shrunk to exclude P13-T02 |
| CY29FCT520-N01-P01 | corrected | pinout re-drawn; kind fixed |
| CY29FCT520-N02-P02 | corrected | block diagram re-drawn from page |
| CY29FCT520-N03-P10 | corrected | drawing retained; positive island recorded |

## Decisions that stay open for the structure design

- **Quadrilateral ruling is table ruling.** `DS10CP152-P13-T02` is fully
  bordered, but every border is a `qu` cell outline. A detector that only
  reads lines and thin rects cannot see it. This is a real failure sample, not
  a gold workaround.
- **Partial sub-rules are visual boundaries, not automatically logical
  columns.** CY29FCT520-P04/P05/P06 and DS10CP152-P04/P05 all have body-only
  sub-rules; the gold keeps them in the visual count and folds them into the
  condition attribute for logical columns.
- **Unlabelled columns are unknown unless content can decide.** The blank
  corner cells in CY29FCT520-P04-T01 and P06 stay `unknown`; P06 column 1 is
  `condition` from its Data/I content and is excluded from header attribution.
- **A negative may contain a positive island.** CY29FCT520-N03-P10 must not be
  scored as a false positive when the parser finds P10 inside it.

## Metric status

The cross-PDF generalization metrics computed against this version are
**internal evaluation results**. They are not an acceptance version: Phase 2
stays frozen and no metric may be packaged as a passed acceptance until the
structure work (Phase 1.4 design) is reviewed. This record establishes that the
gold itself has been independently checked, not that the parser passes.
