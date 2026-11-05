"""Parser configuration loaded from YAML; the effective config is hashed into runs."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from icpdf.storage.artifact_store import sha256_bytes

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[3] / "configs" / "parser.yaml"


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
