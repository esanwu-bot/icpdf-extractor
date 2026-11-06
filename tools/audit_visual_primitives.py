"""Read-only audit of visual boundary evidence against raw PDF primitives.

This is deliberately separate from ``tools.validate_evidence``: the validator
checks the persisted evidence chain, while this audit re-opens the source PDF,
re-runs ``collect_primitives`` and proves that every recorded
``primitive_indices`` entry resolves to a real vertical ruling mark owned by the
recorded ``RuleComponent``.

Index space: ``primitive_indices`` are positions in the list returned by
``collect_primitives(page, page_number, geometry)`` for that page.  They are
*not* ``RulePrimitive.drawing_index`` values.  A drawing can yield zero, one or
four primitives (``quad_edge``), and non-ruling items are skipped, so the two
numberings diverge; on DS10CP152 page 4, 79 of 442 primitives already have
``index != drawing_index``.

Exit status is 1 when any issue is found.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from icpdf.parser.config import TableParams
from icpdf.parser.pdf_loader import load_pdf
from icpdf.parser.rule_primitives import (
    GRID_TOL,
    RuleComponent,
    RulePrimitive,
    build_components,
    collect_primitives,
)

STATUSES = ("printed", "partial", "implied_outer", "not_printed")


@dataclass(frozen=True)
class AuditIssue:
    code: str
    detail: str
    page: int
    boundary_x: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _get(record, key: str, default=None):
    if isinstance(record, dict):
        return record.get(key, default)
    return getattr(record, key, default)


def union_length(spans: list[tuple[float, float]], tol: float) -> float:
    spans = sorted((start, end) for start, end in spans if start < end)
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


def raw_spans(boundary, bbox, primitives: list[RulePrimitive]) -> list[tuple[float, float]]:
    """Spans of the boundary's recorded primitives, clipped to the table."""
    y0, y1 = bbox[1], bbox[3]
    spans: list[tuple[float, float]] = []
    for segment in _get(boundary, "segments", ()) or ():
        for index in _get(segment, "primitive_indices", ()) or ():
            if not isinstance(index, int) or index < 0 or index >= len(primitives):
                continue
            primitive = primitives[index]
            if primitive.orientation != "v":
                continue
            start, end = max(y0, primitive.a), min(y1, primitive.b)
            if end > start:
                spans.append((start, end))
    return spans


def raw_coverage(boundary, bbox, primitives: list[RulePrimitive], *,
                 tol: float) -> float:
    height = bbox[3] - bbox[1]
    if height <= 0:
        return 0.0
    return union_length(raw_spans(boundary, bbox, primitives), tol) / height


def audit_table(table, *, primitives: list[RulePrimitive],
                components: list[RuleComponent],
                params: TableParams | None = None) -> list[AuditIssue]:
    """Audit one table's visual boundary evidence against raw primitives."""
    params = params or TableParams()
    tol = params.visual_boundary_tol_pt
    full = params.visual_full_height_coverage
    span_eps = 1e-6

    page = int(_get(table, "page_number") or 0)
    bbox = tuple(_get(table, "bbox") or (0.0, 0.0, 0.0, 0.0))
    height = bbox[3] - bbox[1]
    components_by_id = {component.component_id: component for component in components}
    region_ids = set(_get(table, "region_components", ()) or ())
    issues: list[AuditIssue] = []

    def add(code: str, detail: str, x: float | None = None) -> None:
        issues.append(AuditIssue(code, detail, page, x))

    for boundary in _get(table, "visual_boundary_evidence", ()) or ():
        x = float(_get(boundary, "x") or 0.0)
        role = _get(boundary, "role")
        segments = list(_get(boundary, "segments", ()) or ())
        listed = sorted(int(value) for value in
                        (_get(boundary, "component_ids", ()) or ()))
        stored_count = int(_get(boundary, "segment_count") or 0)
        if stored_count != len(segments):
            add("SEGMENT_COUNT_MISMATCH",
                f"segment_count={stored_count} but {len(segments)} segments", x)
        if role == "outer_left" and abs(x - bbox[0]) > tol:
            add("OUTER_X_MISMATCH", f"outer_left x={x:.2f} != bbox.x0={bbox[0]:.2f}", x)
        if role == "outer_right" and abs(x - bbox[2]) > tol:
            add("OUTER_X_MISMATCH", f"outer_right x={x:.2f} != bbox.x1={bbox[2]:.2f}", x)

        seen_ids: set[int] = set()
        spans: list[tuple[float, float]] = []
        for segment in segments:
            component_id = _get(segment, "component_id")
            if not isinstance(component_id, int):
                add("SEGMENT_COMPONENT_INVALID", "segment has no integer component_id", x)
                continue
            seen_ids.add(component_id)
            if component_id not in listed:
                add("SEGMENT_COMPONENT_NOT_LISTED",
                    f"component {component_id} is not listed on the boundary", x)
            component = components_by_id.get(component_id)
            if component is None:
                add("COMPONENT_MISSING",
                    f"component {component_id} is not in the rebuilt component set", x)
            elif region_ids and component_id not in region_ids:
                add("COMPONENT_NOT_IN_REGION",
                    f"component {component_id} is not in region_components", x)

            y0 = float(_get(segment, "y0") or 0.0)
            y1 = float(_get(segment, "y1") or 0.0)
            indices = list(_get(segment, "primitive_indices", ()) or ())
            if not indices:
                add("PRIMITIVE_INDEX_MISSING", "segment has no primitive indices", x)
            if indices != sorted(set(indices)):
                add("PRIMITIVE_INDEX_UNSORTED",
                    f"primitive_indices are not ascending/unique: {indices}", x)

            local: list[tuple[float, float]] = []
            for index in indices:
                if not isinstance(index, int) or index < 0 or index >= len(primitives):
                    add("PRIMITIVE_INDEX_OUT_OF_RANGE",
                        f"primitive index {index!r} is outside the page list "
                        f"(size {len(primitives)})", x)
                    continue
                primitive = primitives[index]
                if primitive.page_number != page:
                    add("PRIMITIVE_PAGE_MISMATCH",
                        f"primitive {index} belongs to page {primitive.page_number}", x)
                if primitive.orientation != "v":
                    add("PRIMITIVE_NOT_VERTICAL",
                        f"primitive {index} is {primitive.orientation!r}, not vertical", x)
                if abs(primitive.c - x) > tol:
                    add("PRIMITIVE_X_MISMATCH",
                        f"primitive {index} x={primitive.c:.2f} is {abs(primitive.c - x):.2f}pt "
                        f"from boundary x={x:.2f}", x)
                if component is not None and index not in component.primitive_indices:
                    add("PRIMITIVE_NOT_IN_COMPONENT",
                        f"primitive {index} is not owned by component {component_id}", x)
                start, end = max(bbox[1], primitive.a), min(bbox[3], primitive.b)
                if end <= start:
                    add("PRIMITIVE_OUTSIDE_REGION",
                        f"primitive {index} span [{primitive.a:.2f}, {primitive.b:.2f}] "
                        f"does not intersect the table height", x)
                    continue
                local.append((start, end))
                if start < y0 - span_eps or end > y1 + span_eps:
                    add("PRIMITIVE_OUTSIDE_SEGMENT",
                        f"primitive {index} span [{start:.2f}, {end:.2f}] leaves "
                        f"segment [{y0:.2f}, {y1:.2f}]", x)
            if local:
                envelope = (min(start for start, _ in local),
                            max(end for _, end in local))
                if (abs(envelope[0] - y0) > span_eps
                        or abs(envelope[1] - y1) > span_eps):
                    add("SEGMENT_SPAN_MISMATCH",
                        f"segment span [{y0:.2f}, {y1:.2f}] but its primitives "
                        f"span [{envelope[0]:.2f}, {envelope[1]:.2f}]", x)
            spans.extend(local)

        if sorted(seen_ids) != listed:
            add("COMPONENT_IDS_MISMATCH",
                f"component_ids={listed} but segments come from {sorted(seen_ids)}", x)

        if height <= 0:
            continue
        coverage = union_length(spans, tol) / height
        stored = float(_get(boundary, "coverage") or 0.0)
        drawn = bool(_get(boundary, "drawn"))
        if abs(coverage - stored) > 1e-6:
            add("COVERAGE_MISMATCH",
                f"stored coverage {stored:.6f} but raw primitives give {coverage:.6f}", x)
        if role != "internal" and drawn and coverage < full:
            add("DRAWN_BELOW_FULL",
                f"drawn outer coverage {coverage:.4f} < {full}", x)
        if not drawn and coverage >= full:
            add("IMPLIED_ABOVE_FULL",
                f"implied boundary coverage {coverage:.4f} >= {full}", x)
        if not drawn and segments:
            add("IMPLIED_WITH_SEGMENTS",
                f"implied boundary carries {len(segments)} segments", x)
        if role != "internal" and drawn and not segments:
            add("DRAWN_WITHOUT_SEGMENTS", "drawn outer has no primitive evidence", x)
        if role == "internal" and not drawn:
            add("INTERNAL_NOT_DRAWN", "internal separator is marked undrawn", x)

    return issues


def primitive_index_space(primitives: list[RulePrimitive]) -> dict:
    mismatched = [index for index, primitive in enumerate(primitives)
                  if index != primitive.drawing_index]
    return {
        "primitives": len(primitives),
        "index_ne_drawing_index": len(mismatched),
        "examples": [
            {"index": index, "drawing_index": primitives[index].drawing_index,
             "kind": primitives[index].kind,
             "orientation": primitives[index].orientation}
            for index in mismatched[:3]
        ],
    }


def _iou(left, right) -> float:
    width = min(left[2], right[2]) - max(left[0], right[0])
    height = min(left[3], right[3]) - max(left[1], right[1])
    if width <= 0 or height <= 0:
        return 0.0
    inter = width * height
    area = lambda bbox: max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])
    union = area(left) + area(right) - inter
    return inter / union if union else 0.0


def _table_record(run: Path) -> list[dict]:
    payload = json.loads((run / "tables.json").read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else payload.get("tables", payload)


def _params(run: Path) -> TableParams:
    payload = json.loads((run / "run_config.json").read_text(encoding="utf-8"))
    snapshot = payload.get("table_params") or {}
    return TableParams(**snapshot.get("params", {}))


def audit_run_item(run: Path, item: dict) -> dict:
    page_number = int(item["page"])
    bbox = tuple(item["table"]["bbox"])
    tables = _table_record(run)
    table = max(tables, key=lambda candidate: _iou(tuple(candidate["bbox"]), bbox))
    score = _iou(tuple(table["bbox"]), bbox)
    if score < 0.9:
        raise SystemExit(f"no table matches {item['item_id']} at IoU>=0.9 ({score:.3f})")

    params = _params(run)
    loaded = load_pdf(run / "source.pdf")
    import pymupdf as fitz

    with fitz.open(str(run / "source.pdf")) as document:
        page = document[page_number - 1]
        geometry = loaded.geometries[page_number - 1]
        primitives = collect_primitives(page, page_number, geometry)
        components = build_components(primitives, page_number=page_number,
                                      tol=GRID_TOL,
                                      min_width=params.rule_min_width_pt,
                                      min_height=params.rule_min_height_pt)

    issues = audit_table(table, primitives=primitives, components=components,
                         params=params)
    table_bbox = tuple(table["bbox"])
    boundaries = []
    for boundary in table.get("visual_boundary_evidence") or []:
        boundaries.append({
            "x": boundary["x"],
            "role": boundary["role"],
            "drawn": boundary["drawn"],
            "coverage": boundary["coverage"],
            "recomputed_coverage": raw_coverage(boundary, table_bbox, primitives,
                                                tol=params.visual_boundary_tol_pt),
            "segments": boundary.get("segment_count", 0),
            "primitives": sorted({index for segment in boundary.get("segments") or []
                                  for index in segment.get("primitive_indices") or []}),
            "component_ids": boundary.get("component_ids", []),
        })
    return {
        "run": str(run),
        "item_id": item["item_id"],
        "page": page_number,
        "gold_bbox": list(bbox),
        "table_bbox": list(table_bbox),
        "status": table.get("visual_boundary_status"),
        "visual_columns": table.get("visual_columns"),
        "partial_boundaries": table.get("partial_boundaries", []),
        "primitive_index_space": primitive_index_space(primitives),
        "boundaries": boundaries,
        "issues": [issue.to_dict() for issue in issues],
        "ok": not issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit visual boundary evidence against raw PDF primitives.")
    parser.add_argument("--run", required=True, help="frozen run directory")
    parser.add_argument("--gold", required=True, help="gold JSONL file")
    parser.add_argument("--item-id", required=True, help="gold item id")
    parser.add_argument("--out", help="write the audit result as JSON")
    args = parser.parse_args(argv)

    items = [json.loads(line) for line in
             Path(args.gold).read_text(encoding="utf-8").splitlines() if line.strip()]
    item = next((record for record in items
                 if record["item_id"] == args.item_id), None)
    if item is None:
        raise SystemExit(f"item {args.item_id} not found in {args.gold}")

    result = audit_run_item(Path(args.run), item)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
