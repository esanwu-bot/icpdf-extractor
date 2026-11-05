"""Build the Phase 1.2 gold table set from ``gold/spec.yaml``.

The rule lattice proposes cells; the spec supplies the human decisions that a
lattice cannot make (header depth, logical column splits, canopy merges,
semantic column roles).  Outputs:

* ``gold/gold_table_set.jsonl`` -- one record per table / negative
* ``gold/manifest.json``        -- PDF hashes, counts, baseline commit
* ``gold/overlays/*.png``       -- visual proof for manual review
* ``gold/review.html``          -- review gallery

Usage:
    python -m tools.goldset.annotate
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import yaml

from tools.goldset.rules import build_rule_grid, rule_components

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "gold" / "spec.yaml"
GOLD_DIR = ROOT / "gold"
OVERLAY_DIR = GOLD_DIR / "overlays"
BASELINE_TAG = "phase1.1-baseline"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clean(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def _header_labels(grid, header_rows: int) -> list[str]:
    labels: list[str] = []
    for column in range(len(grid.xs) - 1):
        parts: list[str] = []
        for row in range(header_rows):
            for cell in grid.cells:
                if cell.row == row and cell.column <= column < cell.column + cell.column_span:
                    text = _clean(cell.text)
                    if text:
                        parts.append(text)
                    break
        labels.append(" | ".join(parts))
    return labels


def _review_fields(item: dict, defaults: dict) -> tuple[str, dict]:
    review = {"annotator": defaults["annotator"], "reviewed_at": defaults["reviewed_at"],
              "method": defaults["review_method"],
              "status": "annotator_accepted", "independent_review": "pending"}
    review.update(item.get("review") or {})
    return item.get("verdict", defaults["default_verdict"]), review


def _table_record(item: dict, pdf_meta: dict, defaults: dict) -> dict:
    path = Path(pdf_meta["path"])
    with pymupdf.open(path) as doc:
        page = doc[item["page"] - 1]
        components = rule_components(page)
        index = int(item["component"])
        if index >= len(components):
            raise ValueError(f"{item['id']}: component {index} not found on page "
                             f"{item['page']} ({len(components)} present)")
        component = components[index]
        header_rows = int(item.get("header_rows", 1))
        grid = build_rule_grid(
            page,
            component,
            header_rows=header_rows,
            column_boundaries=item.get("column_boundaries"),
            full_width_rows=set(item.get("full_width_rows") or []),
            merges=[tuple(m) for m in (item.get("merges") or [])],
            no_merge={tuple(m) for m in (item.get("no_merge") or [])},
        )
    n_columns = len(grid.xs) - 1
    n_rows = len(grid.ys) - 1
    verdict, review = _review_fields(item, defaults)
    roles = list(item["column_roles"])
    if len(roles) != n_columns:
        raise ValueError(f"{item['id']}: {len(roles)} column_roles for {n_columns} columns")
    if header_rows >= n_rows:
        raise ValueError(f"{item['id']}: header_rows={header_rows} >= rows={n_rows}")

    cells = [{
        "row": cell.row,
        "column": cell.column,
        "row_span": cell.row_span,
        "column_span": cell.column_span,
        "bbox": [round(v, 2) for v in cell.bbox],
        "text": _clean(cell.text),
        "header": cell.row < header_rows,
    } for cell in grid.cells]
    rows = [{
        "index": row,
        "bbox": [round(grid.xs[0], 2), round(grid.ys[row], 2),
                 round(grid.xs[-1], 2), round(grid.ys[row + 1], 2)],
        "header": row < header_rows,
    } for row in range(n_rows)]

    return {
        "schema_version": "gold-schema/v1",
        "annotation_version": item["_annotation_version"],
        "item_id": item["id"],
        "kind": "table",
        "pdf_id": item["pdf"],
        "pdf_label": pdf_meta["label"],
        "pdf_sha256": pdf_meta["sha256"],
        "page": item["page"],
        "human_verdict": verdict,
        "review": review,
        "notes": item.get("notes", ""),
        "table": {
            "bbox": [round(v, 2) for v in component.bbox],
            "table_type": item["table_type"],
            "header_rows": header_rows,
            "n_rows": n_rows,
            "n_columns": n_columns,
            "n_data_rows": n_rows - header_rows,
            "headers": _header_labels(grid, header_rows),
            "column_roles": roles,
            "column_boundaries": [round(v, 2) for v in grid.xs],
            "row_boundaries": [round(v, 2) for v in grid.ys],
            "rows": rows,
            "cells": cells,
            "cross_page": item.get("cross_page"),
        },
    }


def _negative_record(item: dict, pdf_meta: dict, defaults: dict) -> dict:
    verdict, review = _review_fields(item, defaults)
    return {
        "schema_version": "gold-schema/v1",
        "annotation_version": item["_annotation_version"],
        "item_id": item["id"],
        "kind": "negative",
        "negative_kind": item["negative_kind"],
        "pdf_id": item["pdf"],
        "pdf_label": pdf_meta["label"],
        "pdf_sha256": pdf_meta["sha256"],
        "page": item["page"],
        "human_verdict": verdict,
        "review": review,
        "notes": item.get("notes", ""),
        "bbox": [round(float(v), 2) for v in item["bbox"]],
    }


def _render_overlay(item: dict, record: dict, pdf_meta: dict) -> Path:
    path = Path(pdf_meta["path"])
    with pymupdf.open(path) as doc:
        page = doc[item["page"] - 1]
        if record["kind"] == "table":
            bbox = record["table"]["bbox"]
            for cell in record["table"]["cells"]:
                color = (1.0, 0.55, 0.0) if cell["header"] else (0.0, 0.65, 0.25)
                page.draw_rect(pymupdf.Rect(cell["bbox"]), color=color, width=0.45)
            page.draw_rect(pymupdf.Rect(bbox), color=(0.0, 0.25, 1.0), width=1.4)
            label = f"{record['item_id']}  {record['table']['n_columns']}c x {record['table']['n_rows']}r"
        else:
            bbox = record["bbox"]
            page.draw_rect(pymupdf.Rect(bbox), color=(0.85, 0.0, 0.0), width=1.4, dashes="[4 3] 0")
            label = f"{record['item_id']}  NEGATIVE:{record['negative_kind']}"
        x0, y0, x1, y1 = bbox
        clip = pymupdf.Rect(max(page.rect.x0, x0 - 8), max(page.rect.y0, y0 - 16),
                            min(page.rect.x1, x1 + 8), min(page.rect.y1, y1 + 8))
        page.insert_text((clip.x0 + 3, clip.y0 + 10), label, fontsize=7,
                         color=(0.0, 0.25, 1.0) if record["kind"] == "table" else (0.85, 0.0, 0.0))
        pix = page.get_pixmap(clip=clip, dpi=110)
    target = OVERLAY_DIR / f"{record['item_id']}.png"
    pix.save(str(target))
    return target


def _write_gallery(records: list[dict]) -> None:
    rows = []
    for record in records:
        image = f"overlays/{record['item_id']}.png"
        if record["kind"] == "table":
            table = record["table"]
            detail = (f"{table['n_columns']}c x {table['n_rows']}r "
                      f"(header {table['header_rows']}) · {table['table_type']}")
            roles = ", ".join(table["column_roles"])
            extra = f"<div class='roles'>{roles}</div>"
            if table.get("cross_page"):
                extra += f"<div class='cross'>cross-page {table['cross_page']}</div>"
            css = "table"
        else:
            detail = f"NEGATIVE · {record['negative_kind']}"
            extra = ""
            css = "negative"
        rows.append(
            f"<tr class='{css}'><td><a href='{image}'><img src='{image}' loading='lazy'></a></td>"
            f"<td><b>{record['item_id']}</b><div>{record['pdf_label']} p{record['page']}</div>"
            f"<div>{detail}</div>{extra}<div class='notes'>{record.get('notes','')}</div>"
            f"<div class='verdict'>{record['human_verdict']}</div></td></tr>"
        )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Phase 1.2 Gold Table Set Review</title>
<style>
body{{font-family:system-ui,sans-serif;margin:24px;background:#f6f7f9;color:#111}}
table{{border-collapse:collapse;width:100%}}
tr{{vertical-align:top;border-bottom:1px solid #ccd}}
td{{padding:12px}} td:first-child{{width:58%}}
img{{max-width:100%;border:1px solid #99a;background:#fff}}
.negative img{{border-color:#c33}} .negative .verdict,.table .verdict{{font-weight:600;margin-top:6px}}
.roles{{font-size:12px;color:#345;margin-top:4px}} .cross{{font-size:12px;color:#a30}}
.notes{{font-size:12px;color:#555;margin-top:4px}}
</style></head><body>
<h1>Phase 1.2 Gold Table Set Review</h1>
<p>{len(records)} items · annotation {records[0]['annotation_version']} · overlays: blue = table bbox,
green = body cell, orange = header cell, red dashed = negative region.</p>
<table>{''.join(rows)}</table></body></html>"""
    (GOLD_DIR / "review.html").write_text(html, encoding="utf-8")


def main() -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    annotation_version = spec["annotation_version"]
    defaults = {
        "annotator": spec["annotator"],
        "reviewed_at": spec["reviewed_at"],
        "review_method": spec["review_method"],
        "default_verdict": spec["default_verdict"],
    }
    pdfs = spec["pdfs"]
    for pdf_meta in pdfs.values():
        actual = _sha256(Path(pdf_meta["path"]))
        if actual != pdf_meta["sha256"]:
            raise SystemExit(f"SHA256 mismatch for {pdf_meta['path']}: {actual}")

    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    for item in spec["tables"]:
        item["_annotation_version"] = annotation_version
        records.append(_table_record(item, pdfs[item["pdf"]], defaults))
    for item in spec["negatives"]:
        item["_annotation_version"] = annotation_version
        records.append(_negative_record(item, pdfs[item["pdf"]], defaults))

    with (GOLD_DIR / "gold_table_set.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    for item, record in zip(spec["tables"] + spec["negatives"], records):
        _render_overlay(item, record, pdfs[item["pdf"]])

    _write_gallery(records)

    baseline_commit = subprocess.run(
        ["git", "rev-list", "-n", "1", BASELINE_TAG], cwd=ROOT,
        capture_output=True, text=True, check=False,
    ).stdout.strip()
    manifest = {
        "schema_version": "gold-schema/v1",
        "annotation_version": annotation_version,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "annotator": spec["annotator"],
        "reviewed_at": spec["reviewed_at"],
        "review_method": spec["review_method"],
        "independent_review": "pending",
        "baseline_tag": BASELINE_TAG,
        "baseline_commit": baseline_commit,
        "pdfs": {key: {"label": meta["label"], "path": meta["path"],
                       "sha256": meta["sha256"]} for key, meta in pdfs.items()},
        "counts": {
            "tables": sum(1 for r in records if r["kind"] == "table"),
            "negatives": sum(1 for r in records if r["kind"] == "negative"),
            "negative_kinds": sorted({r["negative_kind"] for r in records if r["kind"] == "negative"}),
            "tables_per_pdf": {key: sum(1 for r in records
                                        if r["kind"] == "table" and r["pdf_id"] == key)
                               for key in pdfs},
        },
        "human_verdicts": {verdict: sum(1 for r in records if r["human_verdict"] == verdict)
                           for verdict in sorted({r["human_verdict"] for r in records})},
    }
    (GOLD_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))
    print(f"wrote {len(records)} records, {len(records)} overlays, gold/review.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
