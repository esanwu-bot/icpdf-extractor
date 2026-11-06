"""Parser configuration loaded from YAML; the effective config is hashed into runs."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from icpdf.storage.artifact_store import sha256_bytes

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "configs" / "parser.yaml"
TABLE_PARAMS_SNAPSHOT_VERSION = "table-params/v2"
SUPPORTED_TABLE_PARAMS_SNAPSHOT_VERSIONS = ("table-params/v1", "table-params/v2")

V1_FIELDS = (
    "cell_gap_pt", "row_gap_factor", "column_tolerance", "header_min_hits",
    "max_title_chars", "max_cell_chars", "min_numeric_cells",
    "rule_min_width_pt", "rule_min_height_pt", "alignment_min_rows",
    "merge_min_gap_pt", "merge_max_gap_pt", "merge_column_tol_pt",
    "merge_min_shared_columns", "merge_shared_ratio", "merge_extent_tol_pt",
    "merge_min_x_overlap_ratio", "visual_min_rule_span_pt",
    "visual_boundary_tol_pt", "visual_full_height_coverage",
)
LOGICAL_FIELDS = (
    "logical_label_min_band_ratio", "logical_label_min_bands",
    "logical_subrule_promote_min_ratio", "logical_subrule_promote_min_bands",
    "logical_subrule_ambiguous_min_ratio", "logical_short_label_max_words",
    "logical_short_label_max_chars",
)
V2_FIELDS = V1_FIELDS + LOGICAL_FIELDS


class PDFConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    render_dpi: int = Field(default=150, ge=36, le=600)
    text_min_chars: int = Field(default=1, ge=0)


class TableParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    cell_gap_pt: float = Field(default=8.0, gt=0)
    row_gap_factor: float = Field(default=2.5, gt=0)
    column_tolerance: int = Field(default=2, ge=0)
    header_min_hits: int = Field(default=2, ge=1)
    max_title_chars: int = Field(default=120, ge=1)
    max_cell_chars: int = Field(default=80, ge=1)
    min_numeric_cells: int = Field(default=2, ge=0)
    rule_min_width_pt: float = Field(default=70.0, gt=0)
    rule_min_height_pt: float = Field(default=15.0, gt=0)
    alignment_min_rows: int = Field(default=3, ge=2)
    # Phase 1.4 S1 - region aggregation.  Additive defaults: they only govern
    # whether physical components are merged, never how a single lattice is
    # parsed, so Phase 1.2 detections keep their existing behaviour.
    merge_min_gap_pt: float = Field(default=2.0, ge=0)
    merge_max_gap_pt: float = Field(default=24.0, gt=0)
    merge_column_tol_pt: float = Field(default=2.5, gt=0)
    merge_min_shared_columns: int = Field(default=2, ge=1)
    merge_shared_ratio: float = Field(default=0.6, gt=0, le=1)
    merge_extent_tol_pt: float = Field(default=3.0, ge=0)
    merge_min_x_overlap_ratio: float = Field(default=0.6, gt=0, le=1)
    # Phase 1.4 S2a - visual boundary lattice.  These govern only the derived
    # visual separators; the recognition lattice (grid.xs/ys) is untouched.
    visual_min_rule_span_pt: float = Field(default=4.0, gt=0)
    visual_boundary_tol_pt: float = Field(default=2.5, gt=0)
    visual_full_height_coverage: float = Field(default=0.85, gt=0, le=1)
    # Phase 1.4 S2b - logical lattice parameters. Code defaults only; the
    # parser YAML stays unchanged, and no logical field enters a v1 snapshot.
    logical_label_min_band_ratio: float = Field(default=0.60, gt=0, le=1)
    logical_label_min_bands: int = Field(default=2, ge=1)
    logical_subrule_promote_min_ratio: float = Field(default=0.50, gt=0, le=1)
    logical_subrule_promote_min_bands: int = Field(default=2, ge=1)
    logical_subrule_ambiguous_min_ratio: float = Field(default=0.25, ge=0, le=1)
    logical_short_label_max_words: int = Field(default=2, ge=1)
    logical_short_label_max_chars: int = Field(default=12, ge=1)


class ParserConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    pdf: PDFConfig = Field(default_factory=PDFConfig)
    tables: TableParams = Field(default_factory=TableParams)


def load_config(path: str | Path | None = None) -> tuple[ParserConfig, str]:
    """Return `(config, sha256(raw bytes))`; the hash is recorded in the run."""
    p = Path(path) if path else DEFAULT_CONFIG_PATH
    raw = p.read_bytes()
    data = yaml.safe_load(raw) or {}
    return ParserConfig(**data), sha256_bytes(raw)


def default_config() -> ParserConfig:
    return ParserConfig()


class UnsupportedTableParamsSnapshotVersion(ValueError):
    """A snapshot version outside the two supported versions was requested."""


class DuplicateTableParamsSnapshotKey(ValueError):
    """A JSON object repeats a key; the parser would otherwise collapse it."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(key)


class TableParamsSnapshotParseError(ValueError):
    """The bytes are not a UTF-8 JSON document."""


@dataclass(frozen=True)
class LoadedTableParamsSnapshot:
    raw: bytes
    document: object


def _table_params_fields(version: str) -> tuple[str, ...]:
    if version == "table-params/v1":
        return V1_FIELDS
    if version == "table-params/v2":
        return V2_FIELDS
    raise UnsupportedTableParamsSnapshotVersion(version)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict:
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            raise DuplicateTableParamsSnapshotKey(key)
        seen.add(key)
    return dict(pairs)


def load_table_params_snapshot(raw: bytes) -> LoadedTableParamsSnapshot:
    """Decode raw snapshot bytes without collapsing duplicate object keys."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TableParamsSnapshotParseError(str(exc)) from exc
    try:
        document = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise TableParamsSnapshotParseError(str(exc)) from exc
    return LoadedTableParamsSnapshot(raw=raw, document=document)


def _field_spec(name: str) -> tuple[type, tuple[tuple[str, float], ...]]:
    field = TableParams.model_fields[name]
    bounds = tuple(
        (attribute, value)
        for meta in field.metadata
        for attribute in ("gt", "ge", "lt", "le")
        if (value := getattr(meta, attribute, None)) is not None
    )
    return field.annotation, bounds


def _value_matches(name: str, value: object) -> bool:
    """JSON type and bound check; never coerces, never treats bool as int."""
    annotation, bounds = _field_spec(name)
    if annotation is int:
        if type(value) is not int:
            return False
    elif annotation is float:
        if type(value) not in (int, float):
            return False
        if type(value) is float and not math.isfinite(value):
            return False
    else:
        raise TypeError(f"unsupported table parameter annotation: {name}")
    for attribute, bound in bounds:
        if attribute == "gt" and not value > bound:
            return False
        if attribute == "ge" and not value >= bound:
            return False
        if attribute == "lt" and not value < bound:
            return False
        if attribute == "le" and not value <= bound:
            return False
    return True


def table_params_snapshot(
        params: TableParams, *,
        version: str = TABLE_PARAMS_SNAPSHOT_VERSION) -> dict:
    """Effective table parameters for one snapshot version."""
    fields = _table_params_fields(version)
    dump = params.model_dump(mode="json")
    selected = {name: dump[name] for name in fields}
    for name, value in selected.items():
        if type(value) is float and not math.isfinite(value):
            raise ValueError(f"non-finite table parameter: {name}")
    return {"snapshot_version": version, "params": selected}


def snapshot_sha256(snapshot: dict) -> str:
    """Hash a parameter snapshot in canonical JSON form."""
    payload = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))


def table_params_sha256(
        params: TableParams, *,
        version: str = TABLE_PARAMS_SNAPSHOT_VERSION) -> str:
    """Hash of the canonical snapshot; recorded next to the values in a run."""
    return snapshot_sha256(table_params_snapshot(params, version=version))


def validate_table_params_snapshot(
        raw: bytes, *, expected_version: str,
        expected_sha256: str) -> list[str]:
    """Strictly validate raw snapshot bytes; returns failure codes, or []."""
    try:
        doc = load_table_params_snapshot(raw)
    except DuplicateTableParamsSnapshotKey:
        return ["table_params_snapshot_duplicate_key"]
    except TableParamsSnapshotParseError:
        return ["table_params_snapshot_parse_error"]
    document = doc.document
    if type(document) is not dict:
        return ["table_params_snapshot_schema_invalid"]
    if set(document) != {"snapshot_version", "params"}:
        return ["table_params_snapshot_schema_invalid"]
    if type(document["params"]) is not dict:
        return ["table_params_snapshot_schema_invalid"]
    version = document["snapshot_version"]
    if not isinstance(version, str) or \
            version not in SUPPORTED_TABLE_PARAMS_SNAPSHOT_VERSIONS:
        return ["unsupported_table_params_snapshot_version"]
    if not isinstance(expected_version, str) or \
            expected_version not in SUPPORTED_TABLE_PARAMS_SNAPSHOT_VERSIONS:
        return ["unsupported_table_params_snapshot_version"]
    if version != expected_version:
        return ["table_params_snapshot_version_mismatch"]
    params = document["params"]
    if set(params) != set(_table_params_fields(version)):
        return ["table_params_snapshot_schema_invalid"]
    for name, value in params.items():
        if not _value_matches(name, value):
            return ["table_params_snapshot_schema_invalid"]
    if snapshot_sha256(document) != expected_sha256:
        return ["table_params_snapshot_sha_mismatch"]
    return []
