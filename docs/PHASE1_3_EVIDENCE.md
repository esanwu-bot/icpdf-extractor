# Phase 1.3 — evidence-chain slice

**Status:** first slice complete; Phase 2 remains frozen.

The Phase 1.2 review accepted detection and semantics but kept Phase 2 closed
until Candidate → Table/Row/Cell/Header/Evidence relations are independently
verifiable.  This slice adds the references and a validator; it does not change
detection, header-depth or role rules.

## Model additions

- `Table.header_cells: list[HeaderCell]` — per column and per header level, the
  printed cell (`header_cell_id`, `level`, `column_id`, `bbox`, `page_number`,
  `source_cell_id`) that produced the label.  A merged canopy can back several
  columns; each reference keeps its own column.
- `TableRow.bbox` — the row box used by containment checks.
- `Candidate.role_source` — `header_text`, `heuristic` or `fail_closed`.
- `Candidate.role_header_cell_id` — header cell backing a `header_text` role.

All fields are optional, so old run artifacts remain readable.

## Validator

`python -m tools.validate_evidence --run runs/<run_id> [--json report.json] [--strict]`

Check families:

| Family | Examples |
| --- | --- |
| Identity | duplicate table/row/cell/candidate/header-cell ids |
| Candidate → table/row/cell | missing table, missing row, cross-table cell, cell not in row, document mismatch |
| Boxes | candidate/cell box mismatch, cell outside row/table/page, table outside page |
| Pages | page_end ordering, cell page outside table range |
| Header | `header_path` length/depth/join, label without a header cell, header cell outside table/page, source cell missing, path/ref text mismatch |
| Role | invalid source, `header_text` role disagreeing with the printed header, missing/unknown header cell, mixed roles in one column |
| Manifest | run/document id, table count, candidate count |

Exit status is 1 on errors; `--strict` also fails on warnings.  Negative tests
cover each family in `tests/unit/test_evidence_validation.py`.

## Run results (parser output unchanged)

| PDF | Tables | Candidates | Header cells | header_text | heuristic | fail_closed | Errors | Warnings |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LM358 | 39 | 5,631 | 272 | 5,218 | 328 | 85 | 0 | 0 |
| ADS1299 | 56 | 2,651 | 354 | 2,369 | 262 | 20 | 0 | 0 |
| ADC12DJ5200 | 301 | 9,328 | 1,609 | 7,207 | 1,015 | 1,106 | 0 | 0 |

The same gold evaluation on the re-parsed runs (`after-5layer-v6-headercells`)
reproduces the Phase 1.2 numbers: TP/FP/FN 46/0/0, row exact 46/46, column exact
44/46, header compact 1.0000, strict 0.9582, header depth 46/46, role 0.9897.
The reference is `runs/phase13_evidence/eval.json` (runs are not committed).

## Known gaps

1. **Cross-page continuation link.**  The validator counts tables that declare
   `page_end > page_number`, but the parser does not yet emit a
   `continues_from` / `continuation_group` relation.  The four cross-page gold
   groups are matched as separate page tables, so the source-page relation is
   not yet represented in the run contract.
2. **Gold v2.**  `docs/GOLD_SPEC.md` separates `visual_boundary` from
   `logical_column`; current v1 still stores a single column count, so the two
   documented mismatches remain.
3. **Role provenance depth.**  `role_source` distinguishes printed-header roles
   from heuristics, but a heuristic role such as an unlabeled condition column
   has no cell-level backing yet; that is intentional fail-closed behaviour.
4. **Generalization.**  No PDF outside the three tuned datasheets has been
   annotated yet.

## Next

- Annotate at least three text-layer vendor PDFs not used for tuning and run
  the frozen parser on them (Micrel MICRF103, National DS10CP152, Cypress
  CY29FCT520 are the current text-layer candidates).
- Decide whether to add a cross-page link to the run contract before or after
  that generalization pass.
