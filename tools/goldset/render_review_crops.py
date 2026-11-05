"""Render standalone PDF crops for an independent gold review.

The crops contain no annotation overlay: the reviewer checks the printed table
or figure first and only then compares it with the gold record.  Usage:

    python -m tools.goldset.render_review_crops \
        --spec gold/generalization/spec.yaml \
        --out-dir gold/generalization/review_crops
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf
import yaml

PADDING = 26.0
ZOOM = 2.6


def _record_bbox(record: dict) -> list[float]:
    if record["kind"] == "table":
        return record["table"]["bbox"]
    return record["bbox"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    records = [json.loads(line) for line in
               (args.spec.parent / "gold_table_set.jsonl").read_text(encoding="utf-8").splitlines()
               if line]
    pdfs = {record["pdf_id"]: record for record in records}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    documents = {}
    try:
        for record in records:
            pdf_id = record["pdf_id"]
            if pdf_id not in documents:
                documents[pdf_id] = pymupdf.open(spec["pdfs"][pdf_id]["path"])
            page = documents[pdf_id][record["page"] - 1]
            x0, y0, x1, y1 = _record_bbox(record)
            clip = pymupdf.Rect(max(page.rect.x0, x0 - PADDING),
                                max(page.rect.y0, y0 - PADDING),
                                min(page.rect.x1, x1 + PADDING),
                                min(page.rect.y1, y1 + PADDING))
            pix = page.get_pixmap(clip=clip, matrix=pymupdf.Matrix(ZOOM, ZOOM))
            target = args.out_dir / f"indep_{record['item_id']}.png"
            pix.save(str(target))
            print(f"{record['item_id']}: {pix.width}x{pix.height}")
    finally:
        for document in documents.values():
            document.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
