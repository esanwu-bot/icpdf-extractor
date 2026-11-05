# -*- coding: utf-8 -*-
"""Negative tests for the run evidence-chain validator."""

from __future__ import annotations

import json
from pathlib import Path

from tools.validate_evidence import main, validate_run

ROLES = ["symbol", "min", "typ", "max"]
TEXTS = ["VOH", "2.4", "3.3", "3.6"]


def _base_run() -> dict:
    headers = ["Symbol", "Min", "Typ", "Max"]
    header_cells = [{
        "header_cell_id": f"t1-h00-c{column:02d}",
        "column_id": column,
        "level": 0,
        "text": headers[column],
        "bbox": [column * 100.0, 0.0, (column + 1) * 100.0, 20.0],
        "page_number": 1,
        "source_cell_id": f"t1-r01-c{column:02d}",
    } for column in range(4)]
    cells = [{
        "cell_id": f"t1-r01-c{column:02d}",
        "row_id": "t1-r01",
        "column_id": column,
        "text": TEXTS[column],
        "bbox": [column * 100.0, 20.0, (column + 1) * 100.0, 40.0],
        "page_number": 1,
        "extraction_method": "table_detector",
        "raw_tokens": [TEXTS[column]],
    } for column in range(4)]
    table = {
        "table_id": "t1",
        "document_id": "doc-1",
        "page_number": 1,
        "page_end": None,
        "bbox": [0.0, 0.0, 400.0, 300.0],
        "title": "Electrical Characteristics",
        "table_type": "electrical_characteristics",
        "headers": headers,
        "header_rows": 1,
        "header_path": [[header] for header in headers],
        "header_cells": header_cells,
        "rows": [{"row_id": "t1-r01", "cells": cells,
                  "bbox": [0.0, 20.0, 400.0, 40.0]}],
        "detection_method": "vector_lines",
        "confidence": 0.9,
        "reconstruction_status": "reconstructed",
        "uncertainty_reason": None,
    }
    candidates = [{
        "candidate_id": f"doc-1:t1-r01-c{column:02d}",
        "document_id": "doc-1",
        "table_id": "t1",
        "row_id": "t1-r01",
        "cell_id": f"t1-r01-c{column:02d}",
        "page_number": 1,
        "bbox": [column * 100.0, 20.0, (column + 1) * 100.0, 40.0],
        "raw_text": TEXTS[column],
        "normalized_value": None,
        "unit": None,
        "column_role": ROLES[column],
        "role_source": "header_text",
        "role_header_cell_id": f"t1-h00-c{column:02d}",
        "candidate_type": "value",
        "extraction_method": "table_detector",
        "source_text_type": "native_pdf_text",
        "reconstruction_status": "reconstructed",
    } for column in range(4)]
    return {
        "tables": [table],
        "candidates": {"run_id": "run-1", "document_id": "doc-1",
                       "candidates": candidates},
        "geometry": [{
            "page_number": 1,
            "mediabox": [0.0, 0.0, 612.0, 792.0],
            "cropbox": [0.0, 0.0, 612.0, 792.0],
            "rect": [0.0, 0.0, 612.0, 792.0],
        }],
        "manifest": {
            "run_id": "run-1",
            "document_id": "doc-1",
            "table_count": 1,
            "candidate_count": 4,
        },
    }


def _write_run(root: Path, data: dict) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "pages").mkdir(exist_ok=True)
    (root / "tables.json").write_text(
        json.dumps(data["tables"], ensure_ascii=False), encoding="utf-8")
    (root / "candidates.json").write_text(
        json.dumps(data["candidates"], ensure_ascii=False), encoding="utf-8")
    (root / "pages" / "geometry.json").write_text(
        json.dumps(data["geometry"], ensure_ascii=False), encoding="utf-8")
    (root / "run_manifest.json").write_text(
        json.dumps(data["manifest"], ensure_ascii=False), encoding="utf-8")
    return root


def _codes(report: dict) -> set[str]:
    return {item["code"] for item in report["errors"]}


def _validated(tmp_path: Path, mutate) -> dict:
    data = _base_run()
    mutate(data)
    return validate_run(_write_run(tmp_path / "run", data))


def test_valid_run_has_no_findings(tmp_path):
    report = _validated(tmp_path, lambda data: None)
    assert report["errors"] == [] and report["warnings"] == []
    assert report["summary"]["header_cells"] == 4
    assert report["summary"]["role_sources"] == {"header_text": 4}


def test_unknown_candidate_table(tmp_path):
    report = _validated(tmp_path, lambda data: data["candidates"]["candidates"][0]
                        .__setitem__("table_id", "missing"))
    assert "CANDIDATE_TABLE_MISSING" in _codes(report)


def test_cross_table_cell_reference(tmp_path):
    def mutate(data):
        data["candidates"]["candidates"][0]["cell_id"] = "t2-r01-c00"
    report = _validated(tmp_path, mutate)
    assert "CANDIDATE_CELL_MISSING" in _codes(report)


def test_candidate_bbox_mismatch(tmp_path):
    def mutate(data):
        data["candidates"]["candidates"][0]["bbox"] = [0, 20, 99, 40]
    assert "CANDIDATE_BBOX_MISMATCH" in _codes(_validated(tmp_path, mutate))


def test_candidate_text_mismatch(tmp_path):
    def mutate(data):
        data["candidates"]["candidates"][0]["raw_text"] = "VOL"
    assert "CANDIDATE_TEXT_MISMATCH" in _codes(_validated(tmp_path, mutate))


def test_cell_outside_page(tmp_path):
    def mutate(data):
        cell = data["tables"][0]["rows"][0]["cells"][0]
        cell["bbox"] = [0.0, 20.0, 700.0, 40.0]
        data["tables"][0]["rows"][0]["bbox"] = [0.0, 20.0, 700.0, 40.0]
        data["candidates"]["candidates"][0]["bbox"] = [0.0, 20.0, 700.0, 40.0]
    report = _validated(tmp_path, mutate)
    assert "CELL_BBOX_OUTSIDE_PAGE" in _codes(report)


def test_row_bbox_does_not_cover_cell(tmp_path):
    def mutate(data):
        data["tables"][0]["rows"][0]["bbox"] = [0.0, 20.0, 150.0, 40.0]
    report = _validated(tmp_path, mutate)
    assert "CELL_BBOX_OUTSIDE_ROW" in _codes(report)


def test_header_path_join_mismatch(tmp_path):
    def mutate(data):
        data["tables"][0]["header_path"][1] = ["Minimum"]
    assert "HEADER_PATH_JOIN" in _codes(_validated(tmp_path, mutate))


def test_header_cell_missing(tmp_path):
    def mutate(data):
        table = data["tables"][0]
        table["header_cells"] = [item for item in table["header_cells"]
                                 if item["column_id"] != 1]
        data["candidates"]["candidates"][1]["role_header_cell_id"] = None
    assert "HEADER_CELL_MISSING" in _codes(_validated(tmp_path, mutate))


def test_header_cell_source_missing(tmp_path):
    def mutate(data):
        data["tables"][0]["header_cells"][0]["source_cell_id"] = "t1-r99-c00"
    assert "HEADER_CELL_SOURCE_MISSING" in _codes(_validated(tmp_path, mutate))


def test_role_header_cell_unknown(tmp_path):
    def mutate(data):
        data["candidates"]["candidates"][0]["role_header_cell_id"] = "t1-h99-c00"
    assert "ROLE_HEADER_CELL_UNKNOWN" in _codes(_validated(tmp_path, mutate))


def test_role_header_text_mismatch(tmp_path):
    def mutate(data):
        data["candidates"]["candidates"][1]["column_role"] = "max"
    assert "ROLE_HEADER_TEXT_MISMATCH" in _codes(_validated(tmp_path, mutate))


def test_role_mixed_in_column(tmp_path):
    def mutate(data):
        candidates = data["candidates"]["candidates"]
        candidates[1]["column_role"] = "max"
        candidates[1]["role_source"] = "heuristic"
        extra = dict(candidates[1])
        extra["candidate_id"] = "doc-1:extra"
        extra["column_role"] = "min"
        candidates.append(extra)
        data["manifest"]["candidate_count"] = 5
    assert "ROLE_MIXED_IN_COLUMN" in _codes(_validated(tmp_path, mutate))


def test_manifest_count_mismatch(tmp_path):
    def mutate(data):
        data["manifest"]["candidate_count"] = 5
    assert "MANIFEST_CANDIDATE_COUNT" in _codes(_validated(tmp_path, mutate))


def test_cli_exit_code_and_json(tmp_path, capsys):
    run = _write_run(tmp_path / "run", _base_run())
    out = tmp_path / "report.json"
    assert main(["--run", str(run), "--json", str(out)]) == 0
    captured = capsys.readouterr()
    assert "errors=0" in captured.out
    assert json.loads(out.read_text(encoding="utf-8"))["summary"]["errors"] == 0
