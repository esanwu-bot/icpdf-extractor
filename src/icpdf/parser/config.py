"""Parser configuration loaded from YAML; the effective config is hashed into runs."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from icpdf.storage.artifact_store import sha256_bytes

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "configs" / "parser.yaml"
TABLE_PARAMS_SNAPSHOT_VERSION = "table-params/v1"


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


def table_params_snapshot(params: TableParams) -> dict:
    """Effective table parameters, including code defaults not in the YAML."""
    return {
        "snapshot_version": TABLE_PARAMS_SNAPSHOT_VERSION,
        "params": params.model_dump(mode="json"),
    }


def snapshot_sha256(snapshot: dict) -> str:
    """Hash a parameter snapshot in canonical JSON form."""
    payload = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))


def table_params_sha256(params: TableParams) -> str:
    """Hash of the canonical snapshot; recorded next to the values in a run."""
    return snapshot_sha256(table_params_snapshot(params))
