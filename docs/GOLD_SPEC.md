# Gold Table Set specification (v2 draft)

This document fixes the annotation conventions that the Phase 1.2 review found
ambiguous.  v1 (`gold-2026-11-06.1`) stays frozen; v2 changes are recorded as a
new annotation version and never overwrite a released one.

## 1. Versioning

- A released gold version is identified by `annotation_version` in
  `gold/spec.yaml`, the git tag that contains it, and an immutable snapshot in
  `gold/versions/<annotation_version>/`.
- `python -m tools.goldset.freeze_version` writes
  `spec.yaml`, `gold_table_set.jsonl`, `manifest.json` and a `VERSION.json`
  with SHA-256 hashes and the source commit.  It refuses to overwrite an
  existing version directory.
- Corrections go into a new version; the previous directory and git tag are
  left untouched.

## 2. Two column representations

A printed table has two different column notions and v1 stored only one of
them.  From v2 every table records both:

- `visual_boundary`: the printed rule/gutter positions.  A condition band that
  covers only part of the table is still a boundary because a reader sees it.
- `logical_column`: the parser's semantic column.  A partial condition band is
  a condition attribute of the columns it covers, not necessarily a new
  logical column.

Rules:

1. `column_count` in the evaluation keeps using `visual_boundary` so the
   metric answers "did the parser reproduce the printed grid?".
2. Semantic metrics (header attribution, column role) use `logical_column`
   and must state that denominator.
3. A table whose only ambiguity is a partial condition band is marked
   `partial_condition_band` with the covered visual spans; reviewers decide the
   logical mapping once per table family (for example, merged for ADS1299 P37,
   split for P70/LM358 P04 until v2 reconciles them).

## 3. Merged cells

- `merged_cells: [[row, column], ...]` marks cells that are printed as one
  region and must not be split into separate data cells.
- `no_merge: [[row, column], ...]` marks boundaries that exist visually but
  must not be treated as logical column splits.
- Header canopies are represented by `header_path` plus per-column
  `header_cells` references; a canopy cell may back several columns.

## 4. Partial condition bands

- A condition band that covers only some columns is recorded as
  `partial_condition_band: {bbox, visual_columns: [...], logical_columns: [...]}`.
- If the annotation cannot decide the logical mapping, the field is present
  with `logical_columns: null` and the table is flagged `ambiguous`.
- Ambiguous tables are excluded from column-count exactness but included in
  detection, row, cell-text and header metrics.

## 5. Unlabeled columns

- Never invent a label for an empty printed header.
- Role `unknown` is the correct fail-closed output.
- A role may only be inferred from layout when the spec records the rule that
  produced it (for example, an unlabeled column left of MIN/TYP/MAX is a
  `condition` column).  The parser records `role_source` and
  `role_header_cell_id`; gold v2 records the same provenance.

## 6. Bit-field diagrams and other negatives

- Bit-field diagrams are negative samples when they are a single register
  drawing without row/column tabular data.
- Register maps with repeated bit columns and per-field rows may be positive
  tables; the decision is recorded per sample with a `kind` and a short reason.
- TOC pages, prose, pin diagrams, charts, timing diagrams, revision history and
  legal notices remain negative by default.
- Schematics (`schematic`), package/mechanical drawings (`drawing`) and
  application/layout diagrams (`layout`) are negative samples even when they
  contain ruled boxes: a box holding a component label or a dimension is not a
  table cell.
- A negative that the parser flags is still a scored false positive.  Negative
  bboxes are annotated tightly so the evaluator can attribute the hit to a
  `negative_kind`.

## 7. Evidence obligations

For every accepted table the gold record keeps:

- table `bbox` and `page`;
- row count and column count in both representations once v2 lands;
- `header_rows` and per-column `header_path`;
- roles per logical column with a provenance field;
- for negatives, the region `bbox` and the rejection reason.

The run-side validator (`tools/validate_evidence.py`) must pass with zero
errors before any metric is reported.
