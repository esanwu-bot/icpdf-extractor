"""Validate the evidence chain of one parse run without re-parsing the PDF.

The validator resolves every candidate back to its table, row, cell and page
box, checks that row/table/header boxes actually contain what they claim, and
checks that header labels and column roles stay tied to printed header cells.
It is intentionally read-only: a run directory is never modified.

Exit status is 1 when any error is found; ``--strict`` also fails on warnings.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from icpdf.parser.header_semantics import role_for_header

TOL = 0.75
ROLE_SOURCES = {"header_text", "heuristic", "fail_closed", "unknown"}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _contains(outer, inner, tol: float = TOL) -> bool:
    return (outer[0] - tol <= inner[0] and outer[1] - tol <= inner[1]
            and outer[2] + tol >= inner[2] and outer[3] + tol >= inner[3])


def _same_bbox(left, right, tol: float = TOL) -> bool:
    return all(abs(a - b) <= tol for a, b in zip(left, right))


def _inside_page(bbox, rect, tol: float = 1.0) -> bool:
    return (bbox[0] >= rect[0] - tol and bbox[1] >= rect[1] - tol
            and bbox[2] <= rect[2] + tol and bbox[3] <= rect[3] + tol)


def _norm(text: str) -> str:
    return " ".join((text or "").split())


class _Report:
    def __init__(self) -> None:
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    def error(self, code: str, detail: str, **ids) -> None:
        self.errors.append({"code": code, "detail": detail, **ids})

    def warning(self, code: str, detail: str, **ids) -> None:
        self.warnings.append({"code": code, "detail": detail, **ids})


def validate_run(run_dir: str | Path) -> dict:
    run_dir = Path(run_dir)
    tables = _load(run_dir / "tables.json")
    candidate_set = _load(run_dir / "candidates.json")
    geometries = {item["page_number"]: item
                  for item in _load(run_dir / "pages" / "geometry.json")}
    manifest = _load(run_dir / "run_manifest.json")
    candidates = candidate_set.get("candidates") or []
    report = _Report()

    if candidate_set.get("run_id") != manifest.get("run_id"):
        report.error("RUN_ID_MISMATCH", "candidates.run_id differs from manifest")
    if candidate_set.get("document_id") != manifest.get("document_id"):
        report.error("DOCUMENT_ID_MISMATCH", "candidates.document_id differs from manifest")
    if manifest.get("table_count") != len(tables):
        report.error("MANIFEST_TABLE_COUNT",
                     f"manifest says {manifest.get('table_count')}, found {len(tables)}")
    if manifest.get("candidate_count") != len(candidates):
        report.error("MANIFEST_CANDIDATE_COUNT",
                     f"manifest says {manifest.get('candidate_count')}, found {len(candidates)}")

    pages = {page: item.get("rect") or item.get("cropbox") or item.get("mediabox")
             for page, item in geometries.items()}
    table_index: dict[str, dict] = {}
    cell_index: dict[tuple[str, str], dict] = {}
    row_index: dict[tuple[str, str], dict] = {}
    header_ids: dict[str, set[str]] = {}
    cross_page = 0

    for table in tables:
        table_id = table["table_id"]
        if table_id in table_index:
            report.error("TABLE_DUPLICATE_ID", "duplicate table_id", table_id=table_id)
            continue
        table_index[table_id] = table
        if table.get("document_id") != manifest.get("document_id"):
            report.error("TABLE_DOCUMENT_MISMATCH",
                         "table document_id differs from manifest", table_id=table_id)
        page_end = table.get("page_end") or table["page_number"]
        if page_end < table["page_number"]:
            report.error("TABLE_PAGE_RANGE", "page_end before page_number",
                         table_id=table_id)
        if page_end > table["page_number"]:
            cross_page += 1
        rect = pages.get(table["page_number"])
        if rect is None:
            report.error("TABLE_PAGE_UNKNOWN", "table page has no geometry",
                         table_id=table_id)
        elif not _inside_page(table["bbox"], rect):
            report.error("TABLE_BBOX_OUTSIDE_PAGE",
                         "table bbox leaves the page box", table_id=table_id)

        row_ids: set[str] = set()
        for row in table.get("rows") or []:
            row_id = row["row_id"]
            if row_id in row_ids:
                report.error("ROW_DUPLICATE_ID", "duplicate row_id",
                             table_id=table_id, row_id=row_id)
            row_ids.add(row_id)
            row_index[(table_id, row_id)] = row
            if row.get("bbox") is None:
                report.warning("ROW_BBOX_MISSING", "row has no bbox",
                               table_id=table_id, row_id=row_id)
            elif not _contains(table["bbox"], row["bbox"]):
                report.error("ROW_BBOX_OUTSIDE_TABLE",
                             "row bbox leaves the table bbox",
                             table_id=table_id, row_id=row_id)
            for cell in row.get("cells") or []:
                cell_id = cell["cell_id"]
                key = (table_id, cell_id)
                if key in cell_index:
                    report.error("CELL_DUPLICATE_ID", "duplicate cell_id",
                                 table_id=table_id, cell_id=cell_id)
                cell_index[key] = cell
                if cell.get("row_id") != row_id:
                    report.error("CELL_ROW_MISMATCH",
                                 "cell row_id differs from its row",
                                 table_id=table_id, cell_id=cell_id)
                if not _contains(table["bbox"], cell["bbox"]):
                    report.error("CELL_BBOX_OUTSIDE_TABLE",
                                 "cell bbox leaves the table bbox",
                                 table_id=table_id, cell_id=cell_id)
                if row.get("bbox") is not None and not _contains(row["bbox"], cell["bbox"]):
                    report.error("CELL_BBOX_OUTSIDE_ROW",
                                 "cell bbox leaves its row bbox",
                                 table_id=table_id, cell_id=cell_id)
                rect = pages.get(cell["page_number"])
                if rect is None:
                    report.error("CELL_PAGE_UNKNOWN", "cell page has no geometry",
                                 table_id=table_id, cell_id=cell_id)
                elif not _inside_page(cell["bbox"], rect):
                    report.error("CELL_BBOX_OUTSIDE_PAGE",
                                 "cell bbox leaves the page box",
                                 table_id=table_id, cell_id=cell_id)
                if not (table["page_number"] <= cell["page_number"] <= page_end):
                    report.error("CELL_PAGE_RANGE", "cell page outside table range",
                                 table_id=table_id, cell_id=cell_id)

        headers = table.get("headers") or []
        header_path = table.get("header_path") or []
        header_rows = int(table.get("header_rows") or 0)
        if header_path and len(header_path) != len(headers):
            report.error("HEADER_PATH_LENGTH",
                         f"{len(header_path)} paths for {len(headers)} headers",
                         table_id=table_id)
        if header_rows and any(len(path) > header_rows for path in header_path):
            report.error("HEADER_PATH_DEPTH", "header path deeper than header_rows",
                         table_id=table_id)
        for column, (label, path) in enumerate(zip(headers, header_path)):
            if " | ".join(path) != label:
                report.error("HEADER_PATH_JOIN",
                             f"path {path!r} does not rebuild {label!r}",
                             table_id=table_id, column=column)

        header_cells = table.get("header_cells") or []
        ids = {item["header_cell_id"] for item in header_cells}
        if len(ids) != len(header_cells):
            report.error("HEADER_CELL_DUPLICATE_ID", "duplicate header_cell_id",
                         table_id=table_id)
        header_ids[table_id] = ids
        by_column: dict[int, list[dict]] = defaultdict(list)
        for item in header_cells:
            column = item["column_id"]
            by_column[column].append(item)
            if not (0 <= column < len(headers)):
                report.error("HEADER_CELL_COLUMN_RANGE",
                             "header cell column outside headers",
                             table_id=table_id, header_cell_id=item["header_cell_id"])
            if header_rows and item["level"] >= header_rows:
                report.error("HEADER_CELL_LEVEL_RANGE",
                             "header cell level outside header_rows",
                             table_id=table_id, header_cell_id=item["header_cell_id"])
            if not _contains(table["bbox"], item["bbox"]):
                report.error("HEADER_CELL_BBOX_OUTSIDE_TABLE",
                             "header cell bbox leaves the table bbox",
                             table_id=table_id, header_cell_id=item["header_cell_id"])
            rect = pages.get(item["page_number"])
            if rect is None or not _inside_page(item["bbox"], rect):
                report.error("HEADER_CELL_BBOX_OUTSIDE_PAGE",
                             "header cell bbox leaves the page box",
                             table_id=table_id, header_cell_id=item["header_cell_id"])
            source_id = item.get("source_cell_id")
            if source_id is not None and (table_id, source_id) not in cell_index:
                report.error("HEADER_CELL_SOURCE_MISSING",
                             f"source cell {source_id} is not in the table",
                             table_id=table_id, header_cell_id=item["header_cell_id"])
        for column, path in enumerate(header_path):
            if not path:
                continue
            cells = sorted(by_column.get(column, []), key=lambda item: item["level"])
            if not cells:
                report.error("HEADER_CELL_MISSING",
                             "column has a label but no header-cell evidence",
                             table_id=table_id, column=column)
                continue
            texts = [_norm(item["text"]) for item in cells]
            if texts != [_norm(part) for part in path]:
                report.error("HEADER_PATH_REF_MISMATCH",
                             f"header cells {texts!r} do not match path {path!r}",
                             table_id=table_id, column=column)

    candidate_ids: set[str] = set()
    roles_by_column: dict[tuple[str, int], set[str]] = defaultdict(set)
    role_sources = Counter()
    for candidate in candidates:
        candidate_id = candidate["candidate_id"]
        if candidate_id in candidate_ids:
            report.error("CANDIDATE_DUPLICATE_ID", "duplicate candidate_id",
                         candidate_id=candidate_id)
        candidate_ids.add(candidate_id)
        table_id = candidate["table_id"]
        table = table_index.get(table_id)
        if table is None:
            report.error("CANDIDATE_TABLE_MISSING", "candidate table not found",
                         candidate_id=candidate_id, table_id=table_id)
            continue
        row = row_index.get((table_id, candidate["row_id"]))
        if row is None:
            report.error("CANDIDATE_ROW_MISSING", "candidate row not found",
                         candidate_id=candidate_id, table_id=table_id)
        cell = cell_index.get((table_id, candidate["cell_id"]))
        if cell is None:
            report.error("CANDIDATE_CELL_MISSING", "candidate cell not found",
                         candidate_id=candidate_id, table_id=table_id)
            continue
        if row is not None and not any(item["cell_id"] == cell["cell_id"]
                                       for item in row.get("cells") or []):
            report.error("CANDIDATE_CELL_ROW_MISMATCH",
                         "cell is not in the candidate row",
                         candidate_id=candidate_id, table_id=table_id)
        if not _same_bbox(candidate["bbox"], cell["bbox"]):
            report.error("CANDIDATE_BBOX_MISMATCH", "candidate bbox differs from cell bbox",
                         candidate_id=candidate_id, table_id=table_id)
        if candidate["page_number"] != cell["page_number"]:
            report.error("CANDIDATE_PAGE_MISMATCH", "candidate page differs from cell page",
                         candidate_id=candidate_id, table_id=table_id)
        if candidate.get("document_id") != manifest.get("document_id"):
            report.error("CANDIDATE_DOCUMENT_MISMATCH",
                         "candidate document differs from manifest",
                         candidate_id=candidate_id)
        if candidate["raw_text"] != cell["text"]:
            report.error("CANDIDATE_TEXT_MISMATCH", "candidate text differs from cell text",
                         candidate_id=candidate_id, table_id=table_id)

        source = candidate.get("role_source", "unknown")
        role_sources[source] += 1
        if source not in ROLE_SOURCES:
            report.error("ROLE_SOURCE_INVALID", f"unknown role_source {source!r}",
                         candidate_id=candidate_id, table_id=table_id)
        column = cell["column_id"]
        roles_by_column[(table_id, column)].add(candidate["column_role"])
        header_cell_id = candidate.get("role_header_cell_id")
        if source == "header_text":
            headers = table.get("headers") or []
            header = headers[column] if column < len(headers) else ""
            expected = role_for_header(header).value
            if candidate["column_role"] != expected:
                report.error("ROLE_HEADER_TEXT_MISMATCH",
                             f"role {candidate['column_role']} but header says {expected}",
                             candidate_id=candidate_id, table_id=table_id)
            if header and not header_cell_id:
                report.error("ROLE_HEADER_CELL_MISSING",
                             "header-derived role has no header cell",
                             candidate_id=candidate_id, table_id=table_id)
        if header_cell_id is not None and header_cell_id not in header_ids.get(table_id, set()):
            report.error("ROLE_HEADER_CELL_UNKNOWN",
                         f"role header cell {header_cell_id} is not in the table",
                         candidate_id=candidate_id, table_id=table_id)
    for (table_id, column), roles in roles_by_column.items():
        if len(roles) > 1:
            report.error("ROLE_MIXED_IN_COLUMN",
                         f"column {column} mixes roles {sorted(roles)}",
                         table_id=table_id, column=column)

    return {
        "run_id": manifest.get("run_id"),
        "document_id": manifest.get("document_id"),
        "tables": len(tables),
        "candidates": len(candidates),
        "errors": report.errors,
        "warnings": report.warnings,
        "summary": {
            "errors": len(report.errors),
            "warnings": len(report.warnings),
            "tables_with_header_cells": sum(1 for table in tables if table.get("header_cells")),
            "header_cells": sum(len(table.get("header_cells") or []) for table in tables),
            "candidates_with_role_header": sum(
                1 for candidate in candidates if candidate.get("role_header_cell_id")),
            "role_sources": dict(role_sources),
            "cross_page_tables": cross_page,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate one icpdf run's evidence chain.")
    parser.add_argument("--run", required=True, help="run directory")
    parser.add_argument("--json", help="write the full report to this path")
    parser.add_argument("--strict", action="store_true", help="fail on warnings too")
    parser.add_argument("--limit", type=int, default=20, help="max findings to print")
    args = parser.parse_args(argv)

    report = validate_run(args.run)
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8", newline="\n")
    summary = report["summary"]
    print(f"run {report['run_id']}  tables={report['tables']}  candidates={report['candidates']}")
    print(f"errors={summary['errors']}  warnings={summary['warnings']}  "
          f"header_cells={summary['header_cells']}  "
          f"role_sources={summary['role_sources']}")
    for label, items in (("ERROR", report["errors"]), ("WARN", report["warnings"])):
        for item in items[:args.limit]:
            print(f"  {label} {item['code']}: {item['detail']}")
        if len(items) > args.limit:
            print(f"  ... {len(items) - args.limit} more {label.lower()}s")
    failed = bool(report["errors"]) or (args.strict and bool(report["warnings"]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
