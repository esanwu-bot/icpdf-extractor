# Phase 1.4 S1 — review response and acceptance evidence

This bundle answers the 8-item checklist and the four `_is_label_grid`
questions.  S2/S3/S4 were not started; nothing was pushed.

## 0. Commits and tree state

| Slice | Commit | Purpose |
| --- | --- | --- |
| S1 | `003311fa8ee24ef68254fa3852329a9a9f1d762a` | original S1 slice; rollback point |
| S1 review follow-up | `3fc45195d8da20d95dd30ef87ef19859d3d2e002` | caption-text gate, narrower label grid, tests, this evidence bundle |

At `3fc4519` the tree was clean (`git status --porcelain` empty).  Patches:

* `003311f_s1.patch` — full `git format-patch -1 003311f` (all S1 code).
* `3fc4519_followup.patch` — review-driven code/test/doc diff only
  (`git diff 003311f 3fc4519 -- src tests tools docs/*.md HANDOFF.md`).

## 1. `rule_primitives.py` diff

New file; see `003311f_s1.patch`.  Review points:

* `collect_primitives` emits `line`, `thin_rect`, and stroked `qu` edges.
  A quad requires `"s" in drawing["type"]` and `weight <= 6.0pt`; fill-only
  and thick quads are skipped.
* Quad edge order is `ul→ur` (top), `ll→lr` (bottom), `ul→ll` (left),
  `ur→lr` (right).  A diagonal quad contributes 12 primitives (4 axis-aligned
  edges per stroke), not 16; the unit test pins this.
* Every primitive retains `page_number, drawing_index, item_index,
  edge_index`, and every merged segment returns `source_indices`.
* `merge_primitives` is the previous collinear clustering plus provenance;
  `build_components` is union-find over touching merged spans.

## 2. `table_regions.py` diff

Full rewrite is in `003311f_s1.patch`; the caption change is in
`3fc4519_followup.patch`.  Current anchors:

| Function | Line | Role |
| --- | --- | --- |
| `_merge_pair` | 168 | structural merge test |
| `_cluster_components` | 215 | seeds + absorption; one cluster emits one region |
| `_union_component` | 251 | union of rules/primitives for the region |
| `_region_from_cluster` | 265 | bbox, implied outer boundary, evidence |
| `detect_table_regions` | 302 | clusters + text-alignment fallback |

Merge conditions (all must hold): x-overlap ≥ 0.6; vertical gap 2–24pt;
≥ 2 shared internal columns and ≥ 60% of each component's columns; widest
horizontal extents align within 3pt; no table/figure caption label in the
gap.  Absorbed members are listed in `region.components` and never emitted as
separate regions; `_cluster_components` breaks after the first absorbing
cluster, so no duplicate output.

**Font size is no longer a condition.**  `_gap_has_caption` (line 126) matches
caption text (`Table`, `Tab.`, `Tabelle`, `Tabla`, `Tableau`, `Tabela`,
`Таблица`, `表`, `표`, `Figure`, `Fig.`, `图`).  `merge_caption_scale` was
removed.  This is the direct answer to concern #2: a 12pt section heading in
the gap still merges, while a body-size caption still splits.

## 3. `header_semantics.py` diff and `_is_label_grid`

Hunk (`3fc4519_followup.patch`):

```python
def _has_description(cells, leading):
    return any(cell is not leading
               and (len(cell.text.split()) >= 3
                    or len(cell.text.strip()) >= 15)
               for cell in cells)

def _is_label_grid(grid):
    ...
    for cells in populated:
        leading = min(cells, key=lambda cell: cell.column)
        if leading.column != 0 or leading.column_span != 1:
            return False
        if not _is_short_label(leading.text):
            return False
        if not _has_description(cells, leading):
            return False
        if len(_nonempty(_row_cells(grid, leading.row))) < 2:
            return False
    return True
```

Admission conditions (all required):

1. `grid.source == "rule_lattice"` (never the text-alignment path).
2. `n_rows >= 3` and `n_columns >= 2`.
3. Every row with any text has ≥ 2 populated cells; a row with exactly one
   populated cell rejects the grid (sparse drawing band).
4. At least 3 such populated rows.
5. The leading cell is in column 0 with `column_span == 1`.
6. The leading cell is a short label: ≤ 12 characters, ≤ 2 words, no
   `.:;!?,`.
7. The same row has a description/value cell: ≥ 3 words or ≥ 15 characters,
   outside the leading cell.

### Answers to the four questions

1. **What makes it a label grid?**  Conditions 1–7 above.  It is a fully
   populated, fully ruled, two-or-more-column key/description grid with no
   header and no numeric requirement.
2. **Does it require a repeated row/column structure?**  Yes.  Every populated
   row must have the same shape (key in column 0 + description), and there must
   be at least three such rows.  It does not require a repeated header row;
   it requires a repeated key/description row shape.
3. **Can prose, pinout or block diagram be mis-collected?**
   * Prose: rejected by condition 6 (the leading cell is a sentence).
   * Sparse drawing bands: rejected by condition 3.
   * Text-alignment output: rejected by condition 1.
   * Two-short-label block diagram: rejected by condition 7.
   * A pinout *table* can still be accepted — it is a table; the CY29 pinout
     *drawing* is still not claimed (`test_cy29_graphics_are_not_claimed_as_solved`,
     N01 expects no candidate).  Scanning all six PDFs, the only grids
     accepted through this exception are the same tape-dimension key table on
     LM358 P42, ADS1299 P78 and DS10 P13; the first two are unannotated pages
     and move no metric.
4. **Negative tests?**  `tests/unit/test_label_grid.py`:
   `test_prose_rows_are_not_a_label_grid`,
   `test_sparse_drawing_bands_are_not_a_label_grid`,
   `test_text_alignment_grids_are_not_label_grids`,
   `test_two_short_label_diagram_is_not_a_label_grid`,
   `test_leading_cell_must_start_at_column_zero`,
   `test_merged_leading_cell_is_not_a_label_grid`,
   `test_two_row_grid_is_not_a_label_grid`; the positive case
   `test_taped_dimension_grid_is_a_label_grid`.  All pass.

## 4. MICRF103 P03 — five components vs final region

* Image: `micrf103_p03_components_vs_region.png` (five colored component
  outlines, blue region `p003-t01`).
* Components JSON: `micrf103_p03_components.json`.  Bboxes:
  `C0 [184.1,186.5,554.9,202.8]`, `C1 [184.1,219.1,554.9,333.6]`,
  `C2 [184.1,349.9,554.9,431.6]`, `C3 [184.1,448.1,554.9,530.0]`,
  `C4 [184.1,546.5,554.9,732.0]`.  Every component has the same five internal
  columns `[184.1,446.9,482.9,518.9,554.9]`.
* Gap labels are all 9.0pt (`Power Supply`, `RF Output Section and Modulation
  Limits:`, `Reference Oscillator Section`, `Digital / Control Section`) —
  section bands, not captions.
* Region: `bbox [46.8,186.48,586.8,732.0]`, `components [0,1,2,3,4]`,
  `boundary_source=implied_horizontal`, merge + absorbed + implied_outer
  evidence (see JSON).

## 5. MICRF103 P03 — internal 30×6 verification

Source: `micrf103_p03_grid.json` and `micrf103_p03_grid_rows.png`.

* `row_count=30`, `column_count=6`.
* Column boundaries `[46.8,184.08,446.88,482.88,518.88,554.88,586.8]` match
  Gold v2 `[46.8,184.1,446.9,482.9,518.9,554.9,586.8]` within 0.02pt.
* 31 row boundaries match Gold v2 exactly within 0.04pt; first row is the
  header (`header_rows=1`, `Parameter | Condition | Min | Typ | Max | Units`).
* Section bands are rows 1, 9, 15, 19.  Each section title is left-aligned in
  column 0, so the reconstructed cell is column 0 with the remaining five
  columns empty.  This is the known S2 merged-cell limitation: they are not
  reconstructed as one full-width cell (`full_width_rows_detected=[]`).
  It does not change the 30×6 mapping, the column set, or any metric.
* No section-local column exists: all five components share the same five
  internal rules, so aggregation did not promote a section-local rule to a
  region-wide column.

## 6. DS10CP152 P13 — cells, mapping, header_rows=0

Table `p013-t01`, bbox `[256.9,213.46,506.36,264.69]`, 5 rows × 2 columns,
`header_rows=0`, `headers ["",""]`, `header_path [[],[]]`, region component
`[1]`, `boundary_source=ruled`.  Quad-only provenance: component 1 has 40
`quad_edge` primitives and 3 vertical rules.

| row | row bbox | c0 bbox | c0 | c1 bbox | c1 |
| --- | --- | --- | --- | --- | --- |
| 0 | 256.90,213.46,506.36,223.57 | 256.90,213.46,275.67,223.57 | A0 | 275.67,213.46,506.36,223.57 | Dimension designed to accommodate the component width |
| 1 | 256.90,223.57,506.36,233.69 | 256.90,223.57,275.67,233.69 | B0 | 275.67,223.57,506.36,233.69 | Dimension designed to accommodate the component length |
| 2 | 256.90,233.69,506.36,243.96 | 256.90,233.69,275.67,243.96 | K0 | 275.67,233.69,506.36,243.96 | Dimension designed to accommodate the component thickness |
| 3 | 256.90,243.96,506.36,253.89 | 256.90,243.96,275.67,253.89 | W | 275.67,243.96,506.36,253.89 | Overall width of the carrier tape |
| 4 | 256.90,253.89,506.36,264.69 | 256.90,253.89,275.67,264.69 | P1 | 275.67,253.89,506.36,264.69 | Pitch between successive cavity centers |

`header_rows=0` is not just a default: the first row `A0 | Dimension ...` is
not header-like (no header vocabulary, one non-numeric key, one descriptive
value), is not a repeated ordinal header, and the grid has no canopy.  The
region is accepted because it satisfies the label-grid gate above; there are
no numeric cells at all, so the numeric gate is bypassed by the exception, not
by a lowered threshold.  Image: `ds10cp152_p13_grid_cells.png`; JSON:
`ds10cp152_p13_grid.json`.

## 7. Required synthetic merge tests

`tests/unit/test_table_regions.py`:

* `test_larger_section_heading_in_gap_still_merges` — same lattice, 12pt
  `Power Supply` heading in the gap → **1 region**.
* `test_caption_text_blocks_merge_even_at_body_size` — `Table 6-1.
  Independent table` at body size 8pt → **2 regions**.
* `test_independent_tables_sharing_columns_do_not_merge` — identical columns
  and extents, 12pt gap, `Table 12. Configuration registers` → **2 regions**,
  both `boundary_source=ruled`.
* `test_section_local_column_does_not_split_other_sections` — one section has
  an extra rule at x=320; the column exists in the region, but rows in the
  section without the rule merge across it, and rows in the section with the
  rule stay split.

All four pass (`26 passed, 2 xfailed` for the S1 test subset; `89 passed,
2 xfailed` full suite).

## 8. Gold v2 and Phase 1.2 per-item diffs

`gold_v2_per_item_diff.json`: all 21 items compared on `matched`, `iou`,
`pred_rows`, `pred_columns`, `pred_table_type`, `gold_rows`, `gold_columns`;
`changed_items=[]`; overall unchanged at TP 21 / FP 4 / FN 0, P 0.8400,
R 1.0000, F1 0.9130; negative FP 4.

`phase12_per_item_diff.json`: all 46 items, `changed_items=[]`; overall
unchanged at TP 46 / FP 0 / FN 0, P/R/F1 1.0, 0 negative FP, 8 out-of-scope.

Review reruns (git-ignored): `runs/phase14_s1/review_rerun/phase12/` and
`runs/phase14_s1/review_rerun/generalization/`.  `tools.validate_evidence
--strict` on all six: `errors=0 warnings=0`.

## 9. Limits and next steps

* Caption detection is a text-convention signal.  Adjacent independent tables
  with an identical lattice and no caption at all remain geometrically
  indistinguishable; that limitation is recorded rather than fixed with a
  vendor branch.
* S2 (visual/logical columns, merged-cell projection including the MICRF
  section bands), S3 (drawing/schematic gate) and S4 (roles/headerless
  semantics) are untouched.  S2 was not started.
* Evidence Validator passing is treated as reference/contract validation only;
  the component, grid and cell JSON above are the independent structural
  evidence for this review.
