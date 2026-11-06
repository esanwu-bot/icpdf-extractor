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
import inspect
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import pymupdf as fitz

import icpdf.parser.rule_primitives as rule_primitives_module
from icpdf.eval.jsonio import (
    JsonMemberDuplicate,
    JsonMemberMissing,
    JsonMemberParseError,
    extract_json_member_bytes,
)
from icpdf.parser.config import (
    TableParams,
    snapshot_sha256,
    validate_table_params_snapshot,
)
from icpdf.parser.layout import rule_components
from icpdf.parser.pdf_loader import file_sha256, load_pdf
from icpdf.parser.rule_primitives import (
    GRID_TOL,
    RuleComponent,
    RulePrimitive,
    build_components,
    collect_primitives,
)

STATUSES = ("printed", "partial", "implied_outer", "not_printed")
REQUIRED_ARTIFACTS = ("document.json", "pages/geometry.json",
                      "tables.json", "run_config.json")
# S1 freeze: last S1 code commit before the S2 design commits.  The hash is the
# content SHA-256 of src/icpdf/parser/rule_primitives.py at that commit
# (``git cat-file blob <commit>:<path> | sha256sum``); the blob is unchanged
# across 003311f..HEAD, so this also identifies the code that generated the
# runs.
S1_FROZEN_COMMIT = "3fc45195d8da20d95dd30ef87ef19859d3d2e002"
S1_FROZEN_RULE_PRIMITIVES_SHA256 = (
    "49e85b601e405b05e585c05a38030b6116b1002e78dab4c2156786ee5a279ab6")


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
        seen_primitives: set[int] = set()
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
            if component is not None:
                if not (component.bbox[0] - tol <= x <= component.bbox[2] + tol):
                    add("COMPONENT_BBOX_MISMATCH",
                        f"boundary x={x:.2f} is outside rebuilt component "
                        f"{component_id} bbox x=[{component.bbox[0]:.2f}, "
                        f"{component.bbox[2]:.2f}]", x)
                if y0 < component.bbox[1] - tol or y1 > component.bbox[3] + tol:
                    add("COMPONENT_BBOX_MISMATCH",
                        f"segment y=[{y0:.2f}, {y1:.2f}] is outside rebuilt "
                        f"component {component_id} bbox y=[{component.bbox[1]:.2f}, "
                        f"{component.bbox[3]:.2f}]", x)
                if not any(abs(vertical.c - x) <= tol
                           for vertical in component.vertical):
                    add("COMPONENT_VERTICAL_MISSING",
                        f"rebuilt component {component_id} has no vertical ruling "
                        f"at x={x:.2f}", x)

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
                if index in seen_primitives:
                    add("PRIMITIVE_DUPLICATE_IN_BOUNDARY",
                        f"primitive {index} is referenced more than once by "
                        f"boundary x={x:.2f}", x)
                seen_primitives.add(index)
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


class AuditIdentityError(RuntimeError):
    """The run directory does not match its recorded identity; refuse to audit."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = tuple(errors)


def _read_json(path: Path) -> dict | list:
    if not path.is_file():
        raise AuditIdentityError([f"missing run artifact: {path.name}"])
    return json.loads(path.read_text(encoding="utf-8"))


def _close(left: float, right: float, tol: float = 1e-6) -> bool:
    return abs(float(left) - float(right)) <= tol


def _artifact_digest(run: Path, entry: dict, name: str,
                     errors: list[str]) -> str | None:
    path = run / name
    if not path.is_file():
        errors.append(f"missing artifact {name}")
        return None
    digest = file_sha256(path)
    if digest != entry.get("sha256"):
        errors.append(f"artifact {name} sha256 {digest} != manifest {entry.get('sha256')}")
    return digest


def grid_tol_binding() -> dict:
    """Record where the component-rebuild tolerance comes from.

    ``GRID_TOL`` is an S1 code constant, not a ``TableParams`` field, so it is
    not covered by the parameter snapshot hash.  The audit therefore imports the
    same symbol the S1 chain uses and verifies that both
    ``build_components`` and ``rule_components`` still default to it.
    """
    source = Path(rule_primitives_module.__file__)
    source_sha = file_sha256(source)
    build_default = inspect.signature(build_components).parameters["tol"].default
    region_default = inspect.signature(rule_components).parameters["tol"].default
    return {
        "symbol": "icpdf.parser.rule_primitives.GRID_TOL",
        "value": GRID_TOL,
        "source_file": str(source),
        "source_sha256": source_sha,
        "s1_frozen_commit": S1_FROZEN_COMMIT,
        "s1_frozen_sha256": S1_FROZEN_RULE_PRIMITIVES_SHA256,
        "frozen_baseline_match": source_sha == S1_FROZEN_RULE_PRIMITIVES_SHA256,
        "build_components_default": build_default,
        "rule_components_default": region_default,
        "s1_defaults_match": build_default == GRID_TOL and region_default == GRID_TOL,
        "in_table_params": "grid_tol" in TableParams.model_fields,
        "covered_by_table_params_sha256": False,
    }


def verify_identity(run: Path) -> dict:
    """Fail closed unless the run directory is the recording it claims to be.

    Checks, in order: artifact hashes, source PDF SHA-256 against the manifest
    document hash, document/page-count/DPI agreement, the parameter snapshot
    hash, and the recorded page geometry against a fresh ``load_pdf`` at the
    recorded DPI (CropBox, rotation and display rect included).
    """
    manifest = _read_json(run / "run_manifest.json")
    config = _read_json(run / "run_config.json")
    document = _read_json(run / "document.json")
    geometry = _read_json(run / "pages" / "geometry.json")
    for name, payload in (("run_manifest.json", manifest),
                          ("run_config.json", config),
                          ("document.json", document)):
        if not isinstance(payload, dict):
            raise AuditIdentityError([f"{name} is not a JSON object"])
    if not isinstance(geometry, list):
        raise AuditIdentityError(["pages/geometry.json is not a page list"])
    errors: list[str] = []

    entries = {artifact.get("name"): artifact
               for artifact in manifest.get("artifacts") or ()}
    missing = [name for name in REQUIRED_ARTIFACTS if name not in entries]
    errors.extend(f"manifest does not record artifact {name}" for name in missing)
    digests = {name: _artifact_digest(run, entries[name], name, errors)
               for name in REQUIRED_ARTIFACTS if name in entries}

    source = run / "source.pdf"
    source_sha = file_sha256(source) if source.is_file() else None
    if source_sha is None:
        errors.append("missing source.pdf")
    if source_sha != manifest.get("document_sha256"):
        errors.append(f"source.pdf sha256 {source_sha} != manifest document_sha256 "
                      f"{manifest.get('document_sha256')}")
    if source_sha != document.get("sha256"):
        errors.append(f"source.pdf sha256 {source_sha} != document.json sha256 "
                      f"{document.get('sha256')}")

    if document.get("page_count") != manifest.get("page_count"):
        errors.append(f"document.json page_count {document.get('page_count')} != "
                      f"manifest {manifest.get('page_count')}")
    if len(geometry) != manifest.get("page_count"):
        errors.append(f"geometry.json has {len(geometry)} pages but manifest records "
                      f"{manifest.get('page_count')}")

    dpi = manifest.get("dpi")
    if not isinstance(dpi, (int, float)) or dpi <= 0:
        errors.append(f"manifest dpi is not a positive number: {dpi!r}")
        dpi = 150.0
    if config.get("dpi") != dpi:
        errors.append(f"run_config dpi {config.get('dpi')} != manifest dpi {dpi}")
    if geometry and any(not _close(page.get("dpi"), dpi) for page in geometry):
        errors.append("recorded page geometry dpi does not match manifest dpi")

    snapshot = manifest.get("table_params") or {}
    config_snapshot = config.get("table_params") or {}
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("params"), dict):
        errors.append("manifest table_params snapshot is not a parameter object")
        snapshot = {}
    if snapshot != config_snapshot:
        errors.append("run_config table_params differ from the manifest snapshot")
    snapshot_hash = snapshot_sha256(snapshot) if snapshot else None
    if snapshot_hash != manifest.get("table_params_sha256"):
        errors.append(f"table_params snapshot sha256 {snapshot_hash} != manifest "
                      f"{manifest.get('table_params_sha256')}")
    if config.get("table_params_sha256") != manifest.get("table_params_sha256"):
        errors.append("run_config table_params_sha256 differs from the manifest")
    if snapshot:
        try:
            snapshot_raw = extract_json_member_bytes(
                (run / "run_manifest.json").read_bytes(), "table_params")
        except JsonMemberDuplicate as exc:
            errors.append(f"table_params_snapshot_duplicate_key: {exc}")
        except JsonMemberMissing as exc:
            errors.append(f"table_params_snapshot_missing: {exc}")
        except JsonMemberParseError as exc:
            errors.append(f"table_params_snapshot_parse_error: {exc}")
        else:
            for code in validate_table_params_snapshot(
                    snapshot_raw,
                    expected_version=snapshot.get("snapshot_version"),
                    expected_sha256=manifest.get("table_params_sha256")):
                errors.append(f"{code}: raw table_params snapshot rejected")
    if config.get("parser_config_sha256") != manifest.get("parser_config_sha256"):
        errors.append("run_config parser_config_sha256 differs from the manifest")
    if config.get("parser_config") != manifest.get("parser_config"):
        errors.append("run_config parser_config differs from the manifest")
    try:
        TableParams(**snapshot.get("params", {}))
    except Exception as exc:                                   # noqa: BLE001
        errors.append(f"table_params snapshot is invalid: {exc}")

    loaded = load_pdf(source, dpi=float(dpi)) if source_sha is not None else None
    if loaded is not None:
        if loaded.document.page_count != manifest.get("page_count"):
            errors.append(f"fresh PDF page_count {loaded.document.page_count} != "
                          f"manifest {manifest.get('page_count')}")
        recorded_sizes = [tuple(size) for size in document.get("page_sizes") or ()]
        fresh_sizes = [tuple(size) for size in loaded.document.page_sizes]
        if recorded_sizes != fresh_sizes:
            errors.append("document.json page_sizes differ from the fresh PDF")
        if list(document.get("page_rotations") or ()) != \
                list(loaded.document.page_rotations):
            errors.append("document.json page_rotations differ from the fresh PDF")
        for index, recorded in enumerate(geometry):
            fresh = loaded.geometries[index]
            for field in ("mediabox", "cropbox", "rect"):
                if tuple(recorded.get(field) or ()) != tuple(getattr(fresh, field)):
                    errors.append(f"page {index + 1} {field} differs from the fresh PDF")
            if int(recorded.get("rotation") or 0) != fresh.rotation:
                errors.append(f"page {index + 1} rotation differs from the fresh PDF")
            if not _close(recorded.get("dpi"), fresh.dpi):
                errors.append(f"page {index + 1} dpi differs from the fresh PDF")

    grid_tol = grid_tol_binding()
    if not grid_tol["s1_defaults_match"]:
        errors.append(
            "GRID_TOL does not match the S1 component defaults: "
            f"constant={grid_tol['value']}, "
            f"build_components={grid_tol['build_components_default']}, "
            f"rule_components={grid_tol['rule_components_default']}")
    if not grid_tol["frozen_baseline_match"]:
        errors.append(
            f"rule_primitives.py sha256 {grid_tol['source_sha256']} does not "
            f"match the S1 frozen baseline {S1_FROZEN_COMMIT} "
            f"({S1_FROZEN_RULE_PRIMITIVES_SHA256})")

    if errors:
        raise AuditIdentityError(errors)
    assert loaded is not None
    return {
        "document_sha256": source_sha,
        "page_count": loaded.document.page_count,
        "dpi": loaded.geometries[0].dpi if loaded.geometries else None,
        "table_params_sha256": snapshot_hash,
        "parser_config_sha256": manifest.get("parser_config_sha256"),
        "table_params": snapshot.get("params", {}),
        "artifacts": digests,
        "grid_tol": grid_tol,
        "pdf": loaded,
    }


def _table_record(run: Path) -> list[dict]:
    payload = json.loads((run / "tables.json").read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else payload.get("tables", payload)


def _segment_spans(segment, bbox, primitives: list[RulePrimitive]
                   ) -> list[tuple[float, float]]:
    spans: list[tuple[float, float]] = []
    for index in _get(segment, "primitive_indices", ()) or ():
        if not isinstance(index, int) or index < 0 or index >= len(primitives):
            continue
        primitive = primitives[index]
        if primitive.orientation != "v":
            continue
        start, end = max(bbox[1], primitive.a), min(bbox[3], primitive.b)
        if end > start:
            spans.append((start, end))
    return spans


def audit_run_item(run: Path, item: dict) -> dict:
    identity = verify_identity(run)
    loaded = identity.pop("pdf")
    params = TableParams(**identity["table_params"])

    page_number = int(item["page"])
    if not 1 <= page_number <= len(loaded.geometries):
        raise AuditIdentityError([f"page {page_number} is outside the document "
                                  f"({len(loaded.geometries)} pages)"])
    bbox = tuple(item["table"]["bbox"])
    tables = _table_record(run)
    table = max(tables, key=lambda candidate: _iou(tuple(candidate["bbox"]), bbox))
    score = _iou(tuple(table["bbox"]), bbox)
    if score < 0.9:
        raise SystemExit(f"no table matches {item['item_id']} at IoU>=0.9 ({score:.3f})")

    with fitz.open(str(run / "source.pdf")) as document:
        page = document[page_number - 1]
        geometry = loaded.geometries[page_number - 1]
        primitives = collect_primitives(page, page_number, geometry)
        components = build_components(primitives, page_number=page_number,
                                      tol=GRID_TOL,
                                      min_width=params.rule_min_width_pt,
                                      min_height=params.rule_min_height_pt)
    components_by_id = {component.component_id: component for component in components}

    issues = audit_table(table, primitives=primitives, components=components,
                         params=params)
    table_bbox = tuple(table["bbox"])
    boundaries = []
    for boundary in table.get("visual_boundary_evidence") or []:
        segments = []
        for segment in boundary.get("segments") or []:
            spans = _segment_spans(segment, table_bbox, primitives)
            segments.append({
                "component_id": segment.get("component_id"),
                "y0": segment.get("y0"),
                "y1": segment.get("y1"),
                "recomputed_y0": min(start for start, _ in spans) if spans else None,
                "recomputed_y1": max(end for _, end in spans) if spans else None,
                "primitive_indices": segment.get("primitive_indices", []),
            })
        boundaries.append({
            "x": boundary["x"],
            "role": boundary["role"],
            "drawn": boundary["drawn"],
            "coverage": boundary["coverage"],
            "recomputed_coverage": raw_coverage(boundary, table_bbox, primitives,
                                                tol=params.visual_boundary_tol_pt),
            "segment_count": boundary.get("segment_count", 0),
            "segments": segments,
            "primitives": sorted({index for segment in boundary.get("segments") or []
                                  for index in segment.get("primitive_indices") or []}),
            "component_ids": boundary.get("component_ids", []),
        })

    used_ids = sorted({int(component_id)
                       for boundary in table.get("visual_boundary_evidence") or []
                       for component_id in boundary.get("component_ids") or []})
    rebuild = {
        "primitives": len(primitives),
        "components": len(components),
        "region_components": list(table.get("region_components") or ()),
        "used_components": [
            {
                "component_id": component_id,
                "bbox": list(components_by_id[component_id].bbox)
                if component_id in components_by_id else None,
                "primitives": len(components_by_id[component_id].primitive_indices)
                if component_id in components_by_id else None,
                "vertical_segments": len(components_by_id[component_id].vertical)
                if component_id in components_by_id else None,
            }
            for component_id in used_ids
        ],
    }
    return {
        "run": str(run),
        "item_id": item["item_id"],
        "page": page_number,
        "gold_bbox": list(bbox),
        "table_bbox": list(table_bbox),
        "identity": identity,
        "rebuild": rebuild,
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

    try:
        result = audit_run_item(Path(args.run), item)
    except AuditIdentityError as error:
        refusal = {
            "run": args.run,
            "item_id": args.item_id,
            "refused": True,
            "identity_errors": list(error.errors),
            "ok": False,
        }
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(
                json.dumps(refusal, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8", newline="\n")
        print(json.dumps(refusal, ensure_ascii=False, indent=2))
        return 2
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
