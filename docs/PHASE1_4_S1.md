# Phase 1.4 S1 — RulePrimitive → RuleComponent → TableRegion

Status: implementation slice S1 complete, local commit only, **awaiting
Reviewer**.  S2/S3/S4 are not started.  Gold v2 (`gen-2026-11-06.2`),
Phase 1.2 rules, the Candidate Registry and the Evidence Validator contracts
are unchanged.

Scope actually delivered:

* **A. RulePrimitive** — one axis-aligned ruling mark from the PDF vector
  stream, for `line`, `thin_rect` and `quad_edge`, with drawing provenance.
* **B. RuleComponent** — connected physical lattice of primitives; carries no
  table claim.
* **C. TableRegion** — aggregation of vertically stacked components that share
  a column lattice, with implied outer boundaries and auditable merge
  evidence.

The parser config file is untouched; every run below reports the frozen
config SHA `ab9f12527767c7dffe670f4b49e516202f224902af996a73eb155aaa420d3d5c`.

## 1. Changed files

| File | Change |
| --- | --- |
| `src/icpdf/parser/rule_primitives.py` | **new**; primitives (line/thin_rect/quad_edge), collinear merge with source indices, union-find components |
| `src/icpdf/parser/layout.py` | re-exports the new model; `page_segments` / `rule_components` now collect quad edges and pass `page_number` |
| `src/icpdf/parser/table_regions.py` | **rewritten aggregation**; merge test, caption block, implied outer boundary, region evidence |
| `src/icpdf/parser/structure.py` | `RegionEvidence`, `TableRegion.components/boundary_source/evidence`; section-local column support for merged regions |
| `src/icpdf/parser/header_semantics.py` | headerless ruled label/description grids accepted (`_is_label_grid`); fixes DS10CP152 P13 |
| `src/icpdf/parser/table_detector.py` | carries `region_components`, `boundary_source`, `merge_evidence` |
| `src/icpdf/parser/table_rebuilder.py` | copies the three region fields into the domain table |
| `src/icpdf/domain/table.py` | additive optional fields `region_components`, `boundary_source`, `merge_evidence` |
| `src/icpdf/parser/config.py` | merge thresholds (defaults only; YAML/config SHA unchanged) |
| `tests/fixtures/synthetic.py` | `quad_ruled_grid`, `stacked_line_sections` fixtures |
| `tests/unit/test_rule_primitives.py` | **new**, 6 tests |
| `tests/unit/test_table_regions.py` | **new**, 6 tests |
| `tests/integration/test_phase14_s1.py` | **new**, required PDF cases (skips when PDFs absent) |
| `tools/render_detection_crops.py` | **new**; run-backed crop with prediction rectangle, no gold overlay |
| `docs/evidence/phase14_s1/*.png` | **new**; detection evidence crops |
| `docs/PHASE1_4_S1.md` | this report |

`git diff --stat` for the nine modified files: 440 insertions, 158 deletions.
Most deletions are the old `page_segments`/`rule_components` bodies moved into
`rule_primitives.py`.

## 2. Data model

### 2.1 RulePrimitive

```text
RulePrimitive
  page_number, kind ("line" | "thin_rect" | "quad_edge"),
  orientation ("h" | "v"), a, b (extent), c (perpendicular position),
  weight, drawing_index, item_index, edge_index
```

* `line`: `l` drawing item; a diagonal line is rejected.
* `thin_rect`: `re` item with one side ≤ 1.6pt; a normal box is rejected.
* `quad_edge`: one edge of a stroked `qu` item; four edges are emitted from
  `quad.ul/ur/ll/lr` in the order top, bottom, left, right.  Fill-only quads
  and quads thicker than 6pt are decoration and are skipped.  Coordinates come
  from the vector drawing, never from text bboxes.

`merge_primitives` performs the same collinear clustering as the previous
line-only implementation and returns each merged span together with the
indices of the primitives that produced it, which is the provenance link.

### 2.2 RuleComponent

```text
RuleComponent
  bbox, horizontal[RuleSegment], vertical[RuleSegment],
  primitives[RulePrimitive], primitive_indices,
  page_number, component_id
```

Built by union-find over touching horizontal/vertical spans; still requires
≥2 horizontals, ≥2 verticals and the minimum 70×15pt density.  A component may
be a table frame, a figure box or a fragment.

### 2.3 TableRegion (detection unit)

```text
TableRegion
  page_number, bbox, source ("rule_lattice" | "text_alignment"),
  component (union component or the single member),
  components[RuleComponent],
  boundary_source ("ruled" | "implied_horizontal" |
                   "implied_alignment" | "mixed"),
  evidence[RegionEvidence]
```

`RegionEvidence` = `kind` (`merge` | `absorbed` | `implied_outer`), `detail`,
`component_ids`, `values`.

Merge test (all must hold):

1. horizontal bbox overlap ratio ≥ 0.6;
2. vertical gap between 2pt and 24pt;
3. shared internal column rules ≥ 2 and ≥ 60% of each component's columns;
4. widest horizontal-rule extents align within 3pt;
5. the gap contains no table/figure caption label ("Table 6-27.", "Tabelle
   6.28", "表 3", ...).  The label text is the signal; font size is
   deliberately ignored, because an in-table section band may be bold or
   larger and some templates set captions at the body size.

Absorbed components are not emitted separately: one cluster produces one
region whose `components` lists every member.  Multi-component regions expand
left/right to the median horizontal-rule extent and record
`boundary_source="implied_horizontal"` plus an `implied_outer` evidence item.
The domain `Table` now exposes the same audit fields (`region_components`,
`boundary_source`, `merge_evidence`); Candidate Registry and Evidence Validator
need no change and validate these runs with 0 errors.

## 3. Tests and real output

```bash
python -m pytest -o addopts="" -q
# 89 passed, 2 xfailed in 8.29s
```

The two xfails are the CY29FCT520 block diagram (P02) and package drawing
(P10): S1 deliberately does not claim the drawing/schematic gate (S3).

```bash
python -m pytest tests/unit/test_rule_primitives.py tests/unit/test_table_regions.py \
                 tests/unit/test_label_grid.py tests/integration/test_phase14_s1.py \
                 -o addopts="" -q
# 26 passed, 2 xfailed
```

Unit coverage: line/thin-rect/quad provenance; diagonal quad ignored; thick
quad ignored; collinear merge keeps both sources; quad grid → one component;
stacked-lattice merge → one region; absorbed component recorded once; caption
text blocks a merge (body-size caption included); a larger section heading in
the gap still merges; two independent tables sharing a lattice do not merge;
section-local columns merge cells in the other sections; different lattice and
zero gap stay separate; single component keeps `ruled`.

`tests/unit/test_label_grid.py` covers the headerless exception: the tape
key/description grid is accepted; prose rows, sparse drawing bands,
text-alignment grids, two-short-label diagrams, a missing column-0 key, a
merged leading cell and two-row grids are rejected.

Integration coverage (PDFs from `gold/generalization/spec.yaml`, skipped if
absent):

* MICRF103 P03 → exactly one region, `bbox≈[46.8,186.5,586.8,732.0]`,
  components `[0,1,2,3,4]`, implied outer boundary, merge+absorbed evidence.
* DS10CP152 P13 → one region `bbox≈[257.4,213.4,505.8,264.0]`, 5 rows ×
  2 columns, header_rows 0, labels `A0 B0 K0 W P1`.
* CY29 pinout → no candidate; block diagram and package drawing → xfail.

## 4. Evidence crops

Rendered from the final runs by `tools/render_detection_crops.py`; blue is the
parser's table bbox, no gold annotation is drawn.

* `docs/evidence/phase14_s1/micrf103_p03_detected.png` — one table spanning the
  five printed sections (p003-t01, IoU 1.0, 30×6).
* `docs/evidence/phase14_s1/ds10cp152_p13_detected.png` — the 5×2 invisible
  (quad-ruled) tape-dimension table (p013-t01, IoU 0.9812).
* Gold v2 independent crops already in the repo:
  `gold/generalization/review_crops/indep_MICRF103-P03-T01.png`,
  `gold/generalization/review_crops/indep_DS10CP152-P13-T02.png`.

Final run artifacts (git-ignored, never overwritten):

| Set | Run |
| --- | --- |
| Phase 1.2 | `runs/phase14_s1/final_phase12/20261106T005850Z-1f87c8` (LM358) |
| Phase 1.2 | `runs/phase14_s1/final_phase12/20261106T005912Z-356a0b` (ADS1299) |
| Phase 1.2 | `runs/phase14_s1/final_phase12/20261106T005936Z-8ba9cc` (ADC12DJ5200) |
| Generalization | `runs/phase14_s1/final_generalization/20261106T010108Z-c15efb` (MICRF103) |
| Generalization | `runs/phase14_s1/final_generalization/20261106T010114Z-5cc138` (DS10CP152) |
| Generalization | `runs/phase14_s1/final_generalization/20261106T010121Z-c17009` (CY29FCT520) |

`tools.validate_evidence --strict` on all six runs: `errors=0 warnings=0`.

## 5. Before / after

### 5.1 Gold v2 (21 tables, 8 negatives)

| | TP | FP | FN | P | R | F1 | negative FP | out-of-scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Phase 1.3 baseline (`eval_v2_internal`) | 19 | 7 | 2 | 0.7308 | 0.9048 | 0.8085 | 4 | 7 |
| S1 final | **21** | **4** | **0** | **0.8400** | **1.0000** | **0.9130** | 4 | 7 |

Only two gold items changed; every other item is byte-identical in
`matched` / `iou` / row and column counts:

| Item | Before | After |
| --- | --- | --- |
| MICRF103-P03-T01 | missed (3 fragments, best IoU 0.2335 in Phase 1.3) | matched, IoU 1.0, 30×6, `implied_outer` exact |
| DS10CP152-P13-T02 | missed (IoU 0.0) | matched, IoU 0.9812, 5×2, header_rows 0, cells 10/10 |

Negative false positives are unchanged (4): CY29 P02 block diagram, CY29 P10
package drawing, DS10 P01 prose, MICRF P04 schematic.  The CY29 P01 pinout FP
present in earlier runs does not occur.

### 5.2 S1 internal rerun (pre-P13 gate fix → final)

Only `DS10CP152-P13-T02` changes (`missed` → `matched`).  Phase 1.2 and Gold v2
negatives are identical, which is the isolation check for the headerless gate.

### 5.3 Phase 1.2 (46 tables, 19 negatives)

| | TP | FP | FN | P | R | F1 | negative FP | out-of-scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Frozen baseline | 46 | 0 | 0 | 1.0 | 1.0 | 1.0 | 0 | 8 |
| S1 final | 46 | 0 | 0 | 1.0 | 1.0 | 1.0 | 0 | 8 |

Per-item check: no Phase 1.2 gold item changed matched status, IoU, row count,
column count or table type.  The two pre-existing column mismatches remain
out of S1 scope (ADS1299-P70-T01 5 vs 4, LM358-P04-T01 6 vs 5).

Two pages outside the Phase 1.2 annotations (LM358 P42, ADS1299 P78) now yield
the same tape-dimension table that DS10 P13 exposes.  They are legitimate
tables, are not on annotated pages, and therefore do not move any metric; they
are reported here for transparency.

## 6. Known defects and left-over work

* **S3 (drawing/schematic gate):** the 4 negative FPs remain.  S1 does not
  attempt prose/diagram rejection; the CY29 pinout, block diagram and package
  drawing are marked xfail, not solved.
* **S2 (visual vs logical columns / cell projection):** CY29 P05 11 vs 9, P06
  6 vs 7, P08 9 vs 12 logical columns; MICRF P03 cell-text F1 0.86 (93 tp, 16
  fp, 15 fn) because merged cells and multi-line bands project words
  differently from gold.  No `condition_path` exists yet.
* **S4 (roles / headerless semantics):** P13 second column is still `unknown`
  (gold `value`); leading-column heuristics still produce symbol/value
  mismatches (CY29 P04/P05/P06, DS10 P03/P07/P11/P13, MICRF P01/P02).
* **Quad coverage:** only stroked `qu` outlines ≤ 6pt are primitives; a
  fill-only cell outline is still invisible.  Axis-aligned edges are required;
  skewed outlines are skipped by design.
* **Merge risk:** the five merge thresholds are structural, but were validated
  on three vendor PDFs plus the three Phase 1.2 PDFs only.  A future vendor
  style may need new evidence, not threshold tuning.
* **Cross-page tables** are still out of scope; the model does not block them,
  but `TableRegion` never spans pages.
* **Rotation/CropBox:** quad edges go through the same display transform as
  lines; the required cases are unrotated pages, so rotated quad grids are
  untested.

No LLM, no OCR, no third-party parser, no per-vendor or per-document branch
was added.  Gold v2 and the frozen Phase 1.2 rules were not modified.

## 7. Reproduce

```bash
export PYTHONPATH=src:. PYTHONIOENCODING=utf-8
python -m pytest -o addopts="" -q
python -m icpdf.cli parse --pdf "<pdf>" --mpn <MPN> --runs runs/phase14_s1/final_phase12
python -m tools.validate_evidence --run <run> --strict
python -m tools.goldset.evaluate \
  --gold gold/generalization/gold_table_set.jsonl \
  --run runs/phase14_s1/final_generalization/20261106T010108Z-c15efb \
  --run runs/phase14_s1/final_generalization/20261106T010114Z-5cc138 \
  --run runs/phase14_s1/final_generalization/20261106T010121Z-c17009 \
  --label phase14-s1-final-gen \
  --out runs/phase14_s1/final_generalization/eval_v2.md \
  --json runs/phase14_s1/final_generalization/eval_v2.json \
  --csv runs/phase14_s1/final_generalization/eval_v2.csv
python -m tools.render_detection_crops \
  --run runs/phase14_s1/final_generalization/20261106T010114Z-5cc138 \
  --page 13 --out docs/evidence/phase14_s1/ds10cp152_p13_detected.png
```

## 8. Reviewer follow-up (2026-11-06)

S1 commit for review: `003311fa8ee24ef68254fa3852329a9a9f1d762a`
(`feat(parser): Phase 1.4 S1 - ruling primitives, components, table regions`).
The follow-up changes below are in a separate commit so the original S1 slice
stays a rollback point.

Two points from the review were implemented, not only documented:

1. **Caption blocking no longer uses font size.** `_gap_has_caption` now
   matches a caption label by text (`Table`, `Tab.`, `Tabelle`, `Tabla`,
   `Tableau`, `Tabela`, `Таблица`, `表`, `표`, `Figure`, `Fig.`, `图`).  A
   synthetic test sets a 12pt section heading in the gap and still merges; a
   second test uses a body-size `Table 12. ...` caption between two tables
   that share columns and asserts they stay separate.  The font-size field
   `merge_caption_scale` was removed (the YAML config and its SHA are
   untouched).
2. **`_is_label_grid` is narrower.** In addition to the previous conditions,
   every populated row must contain a description/value cell (≥3 words or
   ≥15 characters) beside the short column-0 key.  A fully ruled 3×2 grid of
   two short labels per row (block-diagram shape) is now rejected; prose,
   sparse bands, text-alignment grids, merged leading cells and two-row grids
   have explicit negative tests in `tests/unit/test_label_grid.py`.

The review reruns are in `runs/phase14_s1/review_rerun/`; the per-item diff
against the S1 final runs is in `docs/reviews/phase14_s1/`:

* Gold v2: unchanged 21/4/0, P 0.8400, R 1.0, F1 0.9130; `changed_items=[]`.
* Phase 1.2: unchanged 46/0/0, P/R/F1 1.0; `changed_items=[]`.
* Evidence Validator: 6/6 runs `errors=0 warnings=0`.
* Unit/integration: `89 passed, 2 xfailed`.

Review artifacts: `docs/reviews/phase14_s1/REVIEW_RESPONSE.md`,
`micrf103_p03_components_vs_region.png`, `micrf103_p03_grid.json`,
`micrf103_p03_grid_rows.png`, `ds10cp152_p13_grid.json`,
`ds10cp152_p13_grid_cells.png`, `gold_v2_per_item_diff.json`,
`phase12_per_item_diff.json`, plus the full commit patches.
