#!/usr/bin/env python3
"""Phase 1.1 diagnostics: table stats, failure reasons, annotated candidates.

Usage:
    python tools/phase11_audit.py --pdf <pdf> --mpn <mpn> --out <dir> --sample 20
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image, ImageDraw  # noqa: E402

from icpdf.parser.page_renderer import render_page  # noqa: E402
from icpdf.parser.pipeline import parse_pdf  # noqa: E402


def _geom(run_dir: pathlib.Path) -> dict[int, dict]:
    data = json.loads((run_dir / "pages" / "geometry.json").read_text(encoding="utf-8"))
    return {int(g["page_number"]): g for g in data}


def _row_bbox(row: dict) -> tuple:
    cells = row.get("cells") or []
    if not cells:
        return (0.0, 0.0, 0.0, 0.0)
    return (min(c["bbox"][0] for c in cells), min(c["bbox"][1] for c in cells),
            max(c["bbox"][2] for c in cells), max(c["bbox"][3] for c in cells))


def _diagnose(table: dict, page_table_count: int, page_rect: tuple) -> str:
    """Classify why a table is not clean. Diagnostic only; does not change parsing."""
    if table["reconstruction_status"] == "reconstructed":
        return ""
    rows = table.get("rows") or []
    col_counts = [len(r.get("cells") or []) for r in rows]
    if not rows:
        return "not_a_table"
    if len(rows) < 2:
        return "not_a_table"
    long_cells = [c for r in rows for c in r.get("cells") or []
                  if len(str(c.get("text") or "")) > 80]
    if long_cells:
        return "not_a_table"
    if col_counts and max(col_counts) - min(col_counts) >= 2:
        return "merged_cell_uncertain"
    if col_counts and max(col_counts) != min(col_counts):
        return "row_structure_uncertain"
    if table.get("confidence", 1.0) < 0.5:
        return "text_alignment_uncertain"
    x0, y0, x1, y1 = table["bbox"]
    page_h = page_rect[3] - page_rect[1]
    if page_table_count > 3:
        return "table_boundary_uncertain"
    if (y1 - y0) > 0.8 * page_h:
        return "table_boundary_uncertain"
    if y0 - page_rect[1] < 0.12 * page_h and table["page_number"] > 1:
        return "continuation_uncertain"
    return "column_structure_uncertain"


def _sample(cands: list[dict], tables: dict[str, dict], limit: int) -> list[dict]:
    groups = {s: [] for s in ("reconstructed", "partial", "unresolved")}
    for c in cands:
        groups[tables[c["table_id"]]["reconstruction_status"]].append(c)
    quotas = [limit // 3, limit // 3, limit - 2 * (limit // 3)]
    picked: list[dict] = []
    for status, quota in zip(("reconstructed", "partial", "unresolved"), quotas):
        pool = groups[status]
        pool.sort(key=lambda c: (c["page_number"], c["table_id"], c["row_id"], c["cell_id"]))
        if len(pool) <= quota:
            picked.extend(pool)
            continue
        step = len(pool) / quota
        picked.extend(pool[int(i * step)] for i in range(quota))
    if len(picked) < limit:
        rest = [c for c in cands if c not in picked]
        rest.sort(key=lambda c: (c["page_number"], c["table_id"], c["row_id"], c["cell_id"]))
        picked.extend(rest[: limit - len(picked)])
    return picked[:limit]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--mpn", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sample", type=int, default=20)
    a = ap.parse_args()

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "pages").mkdir(exist_ok=True)
    result = parse_pdf(a.pdf, a.mpn, ROOT / "runs" / "phase11_audit")
    run_dir = pathlib.Path(result["run_dir"])
    geoms = _geom(run_dir)
    tables = {t["table_id"]: t for t in
              json.loads((run_dir / "tables.json").read_text(encoding="utf-8"))}
    cands = json.loads((run_dir / "candidates.json").read_text(encoding="utf-8"))["candidates"]

    per_page: dict[int, list[dict]] = {}
    cand_count: dict[str, int] = {}
    for c in cands:
        cand_count[c["table_id"]] = cand_count.get(c["table_id"], 0) + 1
    for t in tables.values():
        per_page.setdefault(t["page_number"], []).append(t)

    # Full table statistics
    with (out / "table_stats.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["page", "table_id", "table_type", "reconstruction_status",
                    "rows", "cols_max", "cols_min", "candidates", "confidence",
                    "bbox", "title", "uncertainty_reason", "diagnostic_reason"])
        for t in tables.values():
            counts = [len(r.get("cells") or []) for r in t.get("rows") or []]
            w.writerow([t["page_number"], t["table_id"], t["table_type"],
                        t["reconstruction_status"], len(t.get("rows") or []),
                        max(counts) if counts else 0, min(counts) if counts else 0,
                        cand_count.get(t["table_id"], 0), t["confidence"],
                        json.dumps(t["bbox"]), t.get("title") or "",
                        t.get("uncertainty_reason") or "",
                        _diagnose(t, len(per_page.get(t["page_number"], [])),
                                  geoms[t["page_number"]]["rect"])])
    with (out / "page_stats.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["page", "table_count", "candidate_count"])
        for page in sorted(per_page):
            w.writerow([page, len(per_page[page]),
                        sum(cand_count.get(t["table_id"], 0) for t in per_page[page])])

    picked = _sample(cands, tables, a.sample)
    pages = sorted({c["page_number"] for c in picked})
    images: dict[int, Image.Image] = {}
    for page in pages:
        png = out / "pages" / f"page-{page:04d}.png"
        geometry = render_page(run_dir / "source.pdf", page, png, dpi=150)
        geoms[page] = json.loads(geometry.model_dump_json())
        images[page] = Image.open(png).convert("RGB")

    def to_px(geom: dict, bbox: tuple) -> tuple:
        z = geom["zoom"]
        return (z * (bbox[0] - geom["rect"][0]), z * (bbox[1] - geom["rect"][1]),
                z * (bbox[2] - geom["rect"][0]), z * (bbox[3] - geom["rect"][1]))

    # Annotated pages: table (blue), row (green), candidate cell (red) + labels
    for page, image in images.items():
        draw = ImageDraw.Draw(image)
        geom = geoms[page]
        for t in per_page.get(page, []):
            draw.rectangle(to_px(geom, t["bbox"]), outline=(0, 90, 220), width=3)
            draw.text((to_px(geom, t["bbox"])[0], to_px(geom, t["bbox"])[1] - 14),
                      f"T {t['table_id']} {t['table_type']} {t['reconstruction_status']}",
                      fill=(0, 90, 220))
            for row in t.get("rows") or []:
                draw.rectangle(to_px(geom, _row_bbox(row)), outline=(0, 160, 60), width=1)
        for index, c in enumerate(picked, 1):
            if c["page_number"] != page:
                continue
            t = tables[c["table_id"]]
            reason = _diagnose(t, len(per_page.get(page, [])), geom["rect"])
            draw.rectangle(to_px(geom, c["bbox"]), outline=(220, 0, 0), width=2)
            draw.text((to_px(geom, c["bbox"])[0], to_px(geom, c["bbox"])[1] - 10),
                      f"#{index} {c['candidate_id']} {c['column_role']}", fill=(220, 0, 0))
            if reason:
                draw.text((to_px(geom, c["bbox"])[0], to_px(geom, c["bbox"])[3] + 2),
                          reason, fill=(150, 0, 150))
        image.save(out / "pages" / f"page-{page:04d}-annotated.png")

    # Contact sheet (5 columns)
    cols, cw, ch, pad = 5, 300, 100, 8
    rows_n = (len(picked) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (cw + pad), rows_n * (ch + pad)), "white")
    draw = ImageDraw.Draw(sheet)
    ink: dict[str, float] = {}
    for index, c in enumerate(picked):
        geom = geoms[c["page_number"]]
        px = to_px(geom, c["bbox"])
        crop = images[c["page_number"]].crop(tuple(round(v) for v in px)).convert("L")
        hist = crop.histogram()
        ink[c["candidate_id"]] = sum(hist[:200]) / max(1, crop.size[0] * crop.size[1])
        x = (index % cols) * (cw + pad)
        y = (index // cols) * (ch + pad)
        t = tables[c["table_id"]]
        reason = _diagnose(t, len(per_page.get(c["page_number"], [])), geom["rect"])
        draw.text((x, y), f"#{index + 1} p{c['page_number']} {t['reconstruction_status']} "
                          f"{c['column_role']} {reason}", fill="black")
        draw.text((x, y + 12), f"{c['raw_text'][:38]}", fill=(80, 80, 80))
        if crop.size[0] > 0 and crop.size[1] > 0:
            thumb = crop.copy()
            thumb.thumbnail((cw, ch - 30))
            sheet.paste(thumb.convert("RGB"), (x, y + 26))
    sheet.save(out / "contact_sheet.png")

    with (out / "audit_candidates.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["idx", "mpn", "page", "table_id", "row_id", "cell_id",
                    "candidate_id", "raw_text", "column_role", "bbox",
                    "table_type", "reconstruction_status", "diagnostic_reason",
                    "table_rows", "table_cols", "table_candidates",
                    "bbox_in_page", "ink_ratio", "verdict", "note"])
        for index, c in enumerate(picked, 1):
            geom = geoms[c["page_number"]]
            rect = geom["rect"]
            inside = (rect[0] <= c["bbox"][0] <= c["bbox"][2] <= rect[2]
                      and rect[1] <= c["bbox"][1] <= c["bbox"][3] <= rect[3])
            t = tables[c["table_id"]]
            counts = [len(r.get("cells") or []) for r in t.get("rows") or []]
            w.writerow([index, a.mpn, c["page_number"], c["table_id"], c["row_id"],
                        c["cell_id"], c["candidate_id"], c["raw_text"],
                        c["column_role"], json.dumps(c["bbox"]), t["table_type"],
                        t["reconstruction_status"],
                        _diagnose(t, len(per_page.get(c["page_number"], [])), rect),
                        len(t.get("rows") or []), max(counts) if counts else 0,
                        cand_count.get(t["table_id"], 0), inside,
                        round(ink[c["candidate_id"]], 4), "", ""])
    status = {}
    for t in tables.values():
        status[t["reconstruction_status"]] = status.get(t["reconstruction_status"], 0) + 1
    unknown = sum(1 for t in tables.values() if t["table_type"] == "unknown")
    print(json.dumps({"run_id": result["run_id"], "pages": result["page_count"],
                      "tables": len(tables), "candidates": len(cands),
                      "status": status, "unknown_type": unknown,
                      "picked": len(picked), "out": str(out)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
