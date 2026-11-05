# Gold Table Set specification (v2)

This document fixes the annotation conventions that the Phase 1.2 review found
ambiguous.  v1 (`gold-2026-11-06.1`) stays frozen; v2 changes are recorded as a
new annotation version and never overwrite a released one.

## 1. Versioning

- A released gold version is identified by `annotation_version` in its
  `spec.yaml`, the git tag that contains it, and an immutable snapshot in
  `<gold-dir>/versions/<annotation_version>/`.
- Gold sets live in more than one directory: the Phase 1.2 set in `gold/` and
  the cross-PDF generalization set in `gold/generalization/`.  Each directory
  has its own `versions/` tree.
- `python -m tools.goldset.freeze_version [--gold-dir DIR]` writes
  `spec.yaml`, `gold_table_set.jsonl`, `manifest.json`, any present
  `PARAMS_FROZEN.json` / `independent_review.json` / `review_record.md`, and a
  `VERSION.json` with SHA-256 hashes and the source commit.  It refuses to
  overwrite an existing version directory and removes a partially written
  snapshot if freezing fails.
- Corrections go into a new version; the previous directory and git tag are
  left untouched.

## 2. Two column representations and four column metrics

A printed table has two different column notions.  v1 stored one count and
alternately described it as visual and as logical; that is the contradiction
this revision removes.  From v2 every table records both:

- `visual_boundary`: a separator a reader can see.  A vertical rule segment of
  any height counts, including a body-only condition sub-rule and a rule that
  spans only part of the table.  The table's outer edges count when they are
  drawn or when the horizontal rules end at that x position.
- `logical_column`: the semantic column used for header attribution and roles.
  A partial condition band is a condition attribute of the columns it covers,
  not necessarily a new logical column.  A logical column may have no printed
  vertical separator (MIN/TYP/MAX sharing a canopy cell, header-label-derived
  columns).

Gold fields per table:

| Field | Meaning |
| --- | --- |
| `visual_columns` | number of printed column intervals; `null` when there is no printed vertical separator to count |
| `visual_boundary_status` | `printed` (all separators drawn), `partial` (at least one separator exists only in some row bands), `implied_outer` (internal separators drawn, outer sides only implied by horizontal rule extents), `not_printed` (no internal vertical separators) |
| `partial_boundaries` | x positions of visual separators that do not span the full table height |
| `logical_columns` | number of semantic columns; `null` when the logical mapping cannot be decided |
| `column_boundaries` | x positions of the logical column boundaries (the grid used for cells) |

Metrics.  A table may be excluded from one metric and included in another; it
is never excluded wholesale because it is "ambiguous".

| Metric | Numerator / denominator | Included when | Excluded and reported as |
| --- | --- | --- | --- |
| Visual boundary exactness | matched tables with `pred_columns == visual_columns`; denominator = matched tables with a comparable visual representation | `visual_boundary_status` is `printed`, `partial` or `implied_outer` | `not_printed` tables (`visual_column_excluded_not_printed`) |
| Logical column exactness | matched tables with `pred_columns == logical_columns`; denominator = matched tables with a decided logical mapping | `logical_columns` is not `null` | undecided mappings (`logical_column_excluded_undecided`) |
| Header attribution | labelled logical columns whose header path matches; denominator = labelled logical columns in tables whose predicted count equals `logical_columns` | table has a decided logical mapping and a predicted count equal to it | unlabelled or unmappable logical columns, counted in `header_unmapped_columns` |
| Role accuracy | logical columns whose role matches; denominator = mapped logical columns in tables whose predicted count equals `logical_columns` | table has a decided logical mapping and a predicted count equal to it | unmappable logical columns, counted in `role_unmapped_columns` |

Consequences:

1. The visual metric answers "did the parser reproduce the printed grid?" and
   keeps partial sub-rules in the gold count even when they are not logical
   columns.
2. Logical column exactness answers "did the parser find the semantic columns?"
   and is the count already reported as `column_count_exact` in v1.
3. Header attribution and role accuracy are always scored on logical columns.
4. A table with `visual_boundary_status: not_printed` (for example a landscape
   packaging table whose columns exist only in the header labels) still counts
   for logical exactness, header attribution and role accuracy.
5. Detection, row count and cell-text metrics always include every accepted
   table, independent of either column representation.

Until the parser emits both representations, both column metrics compare the
parser's single column count against the respective gold count.  The gold
denominators still differ, so the two numbers answer different questions.

## 3. Merged cells and non-merging boundaries

Coordinates are 0-based indices into the **visual** grid of the table.  The two
fields point at different objects and have different shapes:

- `merged_cells` points at **cells**.  A multi-row or multi-column merge is an
  explicit span, not a start coordinate:

  ```yaml
  merged_cells:
    - {row: 0, column: 0, row_span: 2, column_span: 4}   # 2 rows x 4 columns
    - {row: 0, column: 5, row_span: 1, column_span: 2}
  ```

  `row` / `column` are the top-left cell; `row_span` / `column_span` count
  cells and are at least 1.

- `no_merge` points at **boundary segments**, not cells.  It records a printed
  boundary that must not split a logical column (or row) over a range:

  ```yaml
  no_merge:
    - {orientation: vertical, boundary: 2, start: 1, end: 3}
  ```

  `orientation: vertical` indexes `column_boundaries`; `orientation: horizontal`
  indexes `row_boundaries`.  `boundary` is the index of the boundary line.
  `start` / `end` are inclusive indices along the perpendicular axis (rows for
  a vertical boundary, columns for a horizontal one).

- Header canopies use `header_path` plus per-column `header_cells` references;
  a canopy cell may back several logical columns.
- Frozen v1 files keep their legacy forms (`merges: [[row_start, row_end,
  column_start, column_end]]` and `no_merge: [[row, column]]`) because their
  snapshots are immutable.  v2 and later must use the span forms above; the
  annotation tool accepts both while v1 files remain in the repository.

## 4. Partial condition bands

- A condition band that covers only some columns is recorded as
  `partial_condition_band: {bbox, visual_columns: [...], logical_columns: [...]}`.
  `visual_columns` are visual-grid indices, `logical_columns` are logical-grid
  indices, and either list may be empty.
- If the annotation cannot decide the logical mapping, the field is present
  with `logical_columns: null` and `logical_columns` on the table is also
  `null`.
- An undecided logical mapping excludes the table from logical column
  exactness, header attribution and role accuracy.  It does **not** exclude the
  table from detection, row count, cell text or visual boundary exactness.  This
  replaces the v1 sentence that excluded "ambiguous tables" from column-count
  exactness while the same paragraph said the metric used visual boundaries.

## 5. Unlabeled columns

- Never invent a label for an empty printed header.
- Role `unknown` is the correct fail-closed output.
- A role may only be inferred from layout when the spec records the rule that
  produced it (for example, an unlabeled column left of MIN/TYP/MAX is a
  `condition` column).  The parser records `role_source` and
  `role_header_cell_id`; gold v2 records the same provenance.
- A logical column whose printed label cannot be attributed to it is
  `unmapped`; it is excluded from the header and role denominators and counted
  in `header_unmapped_columns` / `role_unmapped_columns`.

## 6. Bit-field diagrams and other negatives

- Bit-field diagrams are negative samples when they are a single register
  drawing without row/column tabular data.
- Register maps with repeated bit columns and per-field rows may be positive
  tables; the decision is recorded per sample with a `kind` and a short reason.
- TOC pages, prose, pin diagrams, charts, timing diagrams, revision history and
  legal notices remain negative by default.
- Schematics (`schematic`), package/mechanical drawings (`drawing`), pinout
  drawings (`pin_diagram`) and application/layout diagrams (`layout`) are
  negative samples even when they contain ruled boxes: a box holding a
  component label or a dimension is not a table cell.
- A negative that the parser flags is still a scored false positive.  Negative
  bboxes are annotated tightly **from the rendered page**, never copied from a
  parser prediction box, so the evaluator can attribute the hit to a
  `negative_kind`.
- A negative region may contain a positive table island (for example a printed
  dimension table inside a package drawing).  Predictions matched to a positive
  table are excluded from negative FP counts; unmatched predictions inside the
  negative region still count.

## 7. Evidence obligations

For every accepted table the gold record keeps:

- table `bbox` and `page`;
- row count, `visual_columns` with its status, and `logical_columns`;
- `column_boundaries`, `row_boundaries` and `partial_boundaries`;
- `header_rows` and per-column `header_path`;
- roles per logical column with a provenance field;
- for negatives, the region `bbox`, the rejection reason and the fact that the
  bbox was drawn from the page rather than from parser output.

The run-side validator (`tools/validate_evidence.py`) must pass with zero
errors before any metric is reported.  Passing the validator proves structural
consistency only; it does not prove that the relations match the printed page.
Visual consistency is established by the independent review described in
`review_record.md`.
