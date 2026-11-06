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

from icpdf.domain.visual import VISUAL_BOUNDARY_ROLES, VISUAL_BOUNDARY_STATUSES
from icpdf.parser.config import snapshot_sha256
from icpdf.parser.header_semantics import role_for_header

TOL = 0.75
ROLE_SOURCES = {"header_text", "heuristic", "fail_closed", "unknown"}
DEFAULT_VISUAL_TOL = 2.5
DEFAULT_VISUAL_FULL = 0.85


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


def _union_length(spans, tol: float) -> float:
    spans = sorted((a, b) for a, b in spans if a < b)
    if not spans:
        return 0.0
    total = 0.0
    start, end = spans[0]
    for next_start, next_end in spans[1:]:
        if next_start <= end + tol:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    return total + (end - start)


def _validate_visual_segments(item: dict, table: dict, report: _Report, *,
                              role: str, tol: float, full: float) -> None:
    """Recompute coverage from the recorded RuleSegment evidence.

    The segments are the clipped vertical spans that fed the boundary; their
    ``component_id`` and page-level ``primitive_indices`` keep the link to the
    RuleComponent/RulePrimitive layer.  ``coverage`` is recomputed here instead
    of being trusted, so two fields cannot simply be wrong together.
    """
    table_id = table["table_id"]
    x = float(item.get("x", 0.0))
    segments = item.get("segments")
    if not isinstance(segments, list):
        report.error("VISUAL_SEGMENTS_MISSING",
                     f"boundary {x:.2f} has no segment evidence", table_id=table_id)
        return
    if int(item.get("segment_count") or 0) != len(segments):
        report.error("VISUAL_SEGMENT_COUNT",
                     f"segment_count={item.get('segment_count')} "
                     f"but {len(segments)} segments", table_id=table_id)
    component_ids = sorted(int(value) for value in (item.get("component_ids") or []))
    seen_ids: set[int] = set()
    ty0, ty1 = table["bbox"][1], table["bbox"][3]
    height = ty1 - ty0
    spans: list[tuple[float, float]] = []
    for segment in segments:
        if not isinstance(segment, dict):
            report.error("VISUAL_SEGMENT_SPAN", "segment is not an object",
                         table_id=table_id)
            continue
        y0 = float(segment.get("y0", 0.0))
        y1 = float(segment.get("y1", 0.0))
        if y1 <= y0 or y0 < ty0 - tol or y1 > ty1 + tol:
            report.error("VISUAL_SEGMENT_SPAN",
                         f"segment [{y0:.2f}, {y1:.2f}] leaves the table height",
                         table_id=table_id)
        spans.append((max(ty0, y0), min(ty1, y1)))
        component_id = segment.get("component_id")
        if not isinstance(component_id, int):
            report.error("VISUAL_SEGMENT_COMPONENT",
                         "segment has no integer component_id", table_id=table_id)
        else:
            seen_ids.add(component_id)
            if component_id not in component_ids:
                report.error("VISUAL_SEGMENT_COMPONENT",
                             f"component {component_id} is not listed on the boundary",
                             table_id=table_id)
        primitives = segment.get("primitive_indices")
        if (not isinstance(primitives, list) or not primitives
                or any(not isinstance(value, int) or value < 0 for value in primitives)
                or primitives != sorted(set(primitives))):
            report.error("VISUAL_SEGMENT_PRIMITIVE",
                         f"boundary {x:.2f} has no valid primitive provenance",
                         table_id=table_id)
    if sorted(seen_ids) != component_ids:
        report.error("VISUAL_COMPONENT_IDS_MISMATCH",
                     f"component_ids={component_ids} but segments come from "
                     f"{sorted(seen_ids)}", table_id=table_id)
    coverage = float(item.get("coverage") or 0.0)
    if height > 0:
        recomputed = min(1.0, _union_length(spans, tol) / height)
        if abs(recomputed - coverage) > 1e-6:
            report.error("VISUAL_COVERAGE_RECOMPUTE",
                         f"boundary {x:.2f} stores coverage {coverage:.6f} "
                         f"but its segments give {recomputed:.6f}",
                         table_id=table_id)
        if bool(item.get("drawn")) and recomputed < full and role != "internal":
            report.error("VISUAL_DRAWN_BELOW_FULL",
                         f"drawn outer boundary {x:.2f} recomputes to "
                         f"{recomputed:.3f}", table_id=table_id)
        if not bool(item.get("drawn")) and recomputed >= full:
            report.error("VISUAL_IMPLIED_ABOVE_FULL",
                         f"implied boundary {x:.2f} recomputes to {recomputed:.3f}",
                         table_id=table_id)


def _validate_visual(table: dict, report: _Report, *, required: bool,
                     tol: float = DEFAULT_VISUAL_TOL,
                     full: float = DEFAULT_VISUAL_FULL) -> None:
    """Reference integrity of the derived visual lattice (S2a).

    This proves internal consistency and traceability, never that a separator
    is semantically the right column boundary.
    """
    table_id = table["table_id"]
    if "visual_boundary_status" not in table:
        if required:
            report.error("VISUAL_STATUS_MISSING",
                         "run records table parameters but the table has no visual status",
                         table_id=table_id)
        return
    status = table.get("visual_boundary_status")
    if status not in VISUAL_BOUNDARY_STATUSES:
        report.error("VISUAL_STATUS_INVALID", f"unknown status {status!r}",
                     table_id=table_id)
        return
    boundaries = table.get("visual_boundaries") or []
    partial = table.get("partial_boundaries") or []
    evidence = table.get("visual_boundary_evidence") or []
    x0, x1 = table["bbox"][0], table["bbox"][2]

    if boundaries != sorted(boundaries):
        report.error("VISUAL_BOUNDARIES_UNSORTED", "visual boundaries are not sorted",
                     table_id=table_id)
    if len({round(x, 3) for x in boundaries}) != len(boundaries):
        report.error("VISUAL_BOUNDARY_DUPLICATE", "duplicate visual boundary",
                     table_id=table_id)
    for x in boundaries:
        if not (x0 - tol <= x <= x1 + tol):
            report.error("VISUAL_BOUNDARY_OUTSIDE_TABLE",
                         f"boundary {x:.2f} leaves the table x-range",
                         table_id=table_id)
    if boundaries:
        if abs(boundaries[0] - x0) > tol:
            report.error("VISUAL_OUTER_LEFT",
                         f"first boundary {boundaries[0]:.2f} is not bbox.x0 {x0:.2f}",
                         table_id=table_id)
        if abs(boundaries[-1] - x1) > tol:
            report.error("VISUAL_OUTER_RIGHT",
                         f"last boundary {boundaries[-1]:.2f} is not bbox.x1 {x1:.2f}",
                         table_id=table_id)

    columns = table.get("visual_columns")
    if status == "not_printed":
        if columns is not None:
            report.error("VISUAL_COLUMNS_NOT_NULL",
                         "not_printed table must carry visual_columns=null",
                         table_id=table_id)
        if partial:
            report.error("VISUAL_NOT_PRINTED_PARTIAL",
                         "not_printed table has partial boundaries", table_id=table_id)
        if len(boundaries) > 2:
            report.error("VISUAL_NOT_PRINTED_INTERNAL",
                         "not_printed table has internal boundaries", table_id=table_id)
    elif columns != len(boundaries) - 1:
        report.error("VISUAL_COLUMNS_MISMATCH",
                     f"visual_columns={columns} but {len(boundaries)} boundaries",
                     table_id=table_id)
    if status == "partial" and not partial:
        report.error("VISUAL_PARTIAL_EMPTY", "partial table lists no partial boundary",
                     table_id=table_id)

    for x in partial:
        if not any(abs(x - boundary) <= tol for boundary in boundaries):
            report.error("VISUAL_PARTIAL_NOT_BOUNDARY",
                         f"partial boundary {x:.2f} is not a visual boundary",
                         table_id=table_id)
        if boundaries and (abs(x - boundaries[0]) <= tol
                           or abs(x - boundaries[-1]) <= tol):
            report.error("VISUAL_PARTIAL_OUTER",
                         f"partial boundary {x:.2f} is an outer edge",
                         table_id=table_id)

    if len(evidence) != len(boundaries):
        report.error("VISUAL_EVIDENCE_COUNT",
                     f"{len(evidence)} evidence records for {len(boundaries)} boundaries",
                     table_id=table_id)
    inner: list[dict] = []
    outer_drawn: list[bool] = []
    for x in boundaries:
        matches = [item for item in evidence if abs(item.get("x", 1e9) - x) <= tol]
        if len(matches) != 1:
            report.error("VISUAL_EVIDENCE_BOUNDARY",
                         f"{len(matches)} evidence records for boundary {x:.2f}",
                         table_id=table_id)
            continue
        item = matches[0]
        role = item.get("role")
        coverage = float(item.get("coverage") or 0.0)
        if role not in VISUAL_BOUNDARY_ROLES:
            report.error("VISUAL_EVIDENCE_ROLE_INVALID", f"unknown role {role!r}",
                         table_id=table_id)
            continue
        if not (0.0 <= coverage <= 1.0):
            report.error("VISUAL_EVIDENCE_COVERAGE",
                         f"coverage {coverage} outside [0, 1]", table_id=table_id)
        _validate_visual_segments(item, table, report, role=role, tol=tol,
                                  full=full)
        if role == "outer_left" and abs(x - x0) > tol:
            report.error("VISUAL_EVIDENCE_ROLE_MISMATCH",
                         "outer_left evidence is not at bbox.x0", table_id=table_id)
        if role == "outer_right" and abs(x - x1) > tol:
            report.error("VISUAL_EVIDENCE_ROLE_MISMATCH",
                         "outer_right evidence is not at bbox.x1", table_id=table_id)
        if role == "internal":
            if not (x0 + tol < x < x1 - tol):
                report.error("VISUAL_EVIDENCE_ROLE_MISMATCH",
                             f"internal evidence {x:.2f} is not strictly inside",
                             table_id=table_id)
            inner.append(item)
            if not item.get("drawn"):
                report.error("VISUAL_INTERNAL_NOT_DRAWN",
                             "internal boundary has no printed rule", table_id=table_id)
            is_partial = any(abs(x - value) <= tol for value in partial)
            if is_partial and coverage >= full:
                report.error("VISUAL_PARTIAL_COVERAGE",
                             f"partial boundary {x:.2f} covers {coverage:.3f}",
                             table_id=table_id)
            if not is_partial and coverage < full:
                report.error("VISUAL_FULL_COVERAGE",
                             f"non-partial boundary {x:.2f} covers only {coverage:.3f}",
                             table_id=table_id)
        else:
            expected = coverage >= full
            if bool(item.get("drawn")) != expected:
                report.error("VISUAL_OUTER_EVIDENCE_INCONSISTENT",
                             f"{role} drawn={item.get('drawn')} at coverage {coverage:.3f}",
                             table_id=table_id)
            outer_drawn.append(bool(item.get("drawn")))

    if status == "not_printed" and inner:
        report.error("VISUAL_NOT_PRINTED_EVIDENCE",
                     "not_printed table has internal evidence", table_id=table_id)
    if status == "printed" and not all(outer_drawn):
        report.error("VISUAL_PRINTED_OUTER_IMPLIED",
                     "printed table has an implied outer edge", table_id=table_id)
    if status == "implied_outer" and all(outer_drawn):
        report.error("VISUAL_IMPLIED_OUTER_DRAWN",
                     "implied_outer table has both outer edges drawn",
                     table_id=table_id)


def validate_run(run_dir: str | Path) -> dict:
    run_dir = Path(run_dir)
    tables = _load(run_dir / "tables.json")
    candidate_set = _load(run_dir / "candidates.json")
    geometries = {item["page_number"]: item
                  for item in _load(run_dir / "pages" / "geometry.json")}
    manifest = _load(run_dir / "run_manifest.json")
    candidates = candidate_set.get("candidates") or []
    report = _Report()

    params_snapshot = manifest.get("table_params")
    visual_params = (params_snapshot or {}).get("params") or {}
    visual_tol = float(visual_params.get("visual_boundary_tol_pt", DEFAULT_VISUAL_TOL))
    visual_full = float(visual_params.get("visual_full_height_coverage",
                                          DEFAULT_VISUAL_FULL))
    if params_snapshot is not None:
        if manifest.get("table_params_sha256") != snapshot_sha256(params_snapshot):
            report.error("PARAM_SNAPSHOT_HASH",
                         "table_params_sha256 does not match the parameter snapshot")
        config_path = run_dir / "run_config.json"
        if config_path.exists():
            config = _load(config_path)
            if (config.get("table_params") != params_snapshot
                    or config.get("table_params_sha256")
                    != manifest.get("table_params_sha256")):
                report.error("CONFIG_PARAMS_MISMATCH",
                             "run_config table parameters differ from the manifest")

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

        _validate_visual(table, report, required=params_snapshot is not None,
                         tol=visual_tol, full=visual_full)

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
            "visual_boundary_status": dict(Counter(
                table.get("visual_boundary_status", "absent") for table in tables)),
            "visual_columns_null": sum(1 for table in tables
                                       if table.get("visual_columns") is None),
            "table_params_sha256": manifest.get("table_params_sha256"),
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
    print(f"visual={summary['visual_boundary_status']}  "
          f"visual_columns_null={summary['visual_columns_null']}  "
          f"table_params_sha256={summary['table_params_sha256']}")
    for label, items in (("ERROR", report["errors"]), ("WARN", report["warnings"])):
        for item in items[:args.limit]:
            print(f"  {label} {item['code']}: {item['detail']}")
        if len(items) > args.limit:
            print(f"  ... {len(items) - args.limit} more {label.lower()}s")
    failed = bool(report["errors"]) or (args.strict and bool(report["warnings"]))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
