"""Phase 1 pipeline: PDF → text blocks → tables → candidates → run artifacts."""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

import pymupdf as fitz

from icpdf import PARSER_VERSION, __version__
from icpdf.domain import Product
from icpdf.domain.candidate import ColumnRole
from icpdf.parser.candidate_registry import build_candidates
from icpdf.parser.config import load_config
from icpdf.parser.page_renderer import render_page
from icpdf.parser.pdf_loader import LoadedPDF, load_pdf
from icpdf.parser.table_detector import detect_tables
from icpdf.parser.table_rebuilder import build_table
from icpdf.parser.text_blocks import extract_text_blocks
from icpdf.storage.run_store import RunStore

CONTRACT_VERSION = "data-contract/v0.2"


def _sanitized_config(requested_mpn: str, dpi: float, config, config_sha: str) -> dict:
    """Never write secret values into a run artifact."""
    return {
        "requested_mpn": requested_mpn,
        "dpi": dpi,
        "parser_config": config.model_dump(mode="json"),
        "parser_config_sha256": config_sha,
        "llm": {
            "provider": "dashscope",
            "model": os.getenv("ICPDF_LLM_MODEL", ""),
            "timeout": os.getenv("ICPDF_LLM_TIMEOUT", ""),
            "api_key_present": bool(os.getenv("DASHSCOPE_API_KEY")),
        },
        "contract_version": CONTRACT_VERSION,
        "parser_version": PARSER_VERSION,
    }


def parse_pdf(pdf_path: str | Path, requested_mpn: str,
              runs_root: str | Path = "runs", *, dpi: float | None = None,
              run_id: str | None = None, config_path: str | Path | None = None) -> dict:
    config, config_sha = load_config(config_path)
    effective_dpi = float(dpi) if dpi else float(config.pdf.render_dpi)
    loaded: LoadedPDF = load_pdf(pdf_path, dpi=effective_dpi)
    document = loaded.document
    run = RunStore.create(runs_root, run_id)
    source_sha = run.copy_source(loaded.path)

    run.write_json("document.json", document.model_dump(mode="json"))
    run.write_json("pages/geometry.json",
                   [g.model_dump(mode="json") for g in loaded.geometries])

    all_blocks: list[dict] = []
    all_tables = []
    table_roles: dict[str, list[ColumnRole]] = {}
    detection_methods: dict[str, int] = {}
    rendered_pages: list[int] = []
    with fitz.open(str(loaded.path)) as doc:
        for page_index, page in enumerate(doc):
            page_number = page_index + 1
            geometry = loaded.geometries[page_index]
            blocks = extract_text_blocks(page, page_number, geometry)
            all_blocks.extend(block.model_dump(mode="json") for block in blocks)
            detected = detect_tables(blocks, page_number, config.tables,
                                     page=page, geometry=geometry)
            if detected:
                rendered_pages.append(page_number)
                render_page(loaded.path, page_number,
                            run.dir / "pages" / f"page-{page_number:04d}.png",
                            dpi=effective_dpi)
            for index, item in enumerate(detected, 1):
                table = build_table(item, document.document_id, index)
                all_tables.append(table)
                table_roles[table.table_id] = [ColumnRole(role) for role in item.column_roles]
                detection_methods[item.detection_method] = \
                    detection_methods.get(item.detection_method, 0) + 1

    run.write_json("text_blocks.json", all_blocks)
    run.write_json("tables.json", [t.model_dump(mode="json") for t in all_tables])
    candidates = build_candidates(run.run_id, document.document_id, all_tables, table_roles)
    run.write_json("candidates.json", candidates.model_dump(mode="json"))

    product = Product(
        product_id=f"prod-{document.document_id}",
        document_id=document.document_id,
        requested_mpn=requested_mpn,
        normalized_mpn=requested_mpn,
        identity_scope="unknown",
        product_type="unknown",
    )
    run.write_json("product.json", product.model_dump(mode="json"))
    run.write_json("run_config.json",
                   _sanitized_config(requested_mpn, effective_dpi, config, config_sha))

    manifest = run.write_manifest({
        "run_id": run.run_id,
        "document_id": document.document_id,
        "document_sha256": source_sha,
        "requested_mpn": requested_mpn,
        "python_version": sys.version.split()[0],
        "project_version": __version__,
        "parser_version": PARSER_VERSION,
        "contract_version": CONTRACT_VERSION,
        "parser_config": config.model_dump(mode="json"),
        "parser_config_sha256": config_sha,
        "platform": platform.platform(),
        "dpi": effective_dpi,
        "page_count": document.page_count,
        "table_count": len(all_tables),
        "candidate_count": len(candidates.candidates),
        "detection_methods": detection_methods,
        "rendered_pages": rendered_pages,
        "model": os.getenv("ICPDF_LLM_MODEL", ""),
        "prompt_version": "",
    })
    return {
        "run_id": run.run_id,
        "run_dir": str(run.dir),
        "document_id": document.document_id,
        "document_sha256": source_sha,
        "page_count": document.page_count,
        "tables": len(all_tables),
        "candidates": len(candidates.candidates),
        "manifest_sha256": manifest["sha256"],
    }
