"""Render a page crop with the tables detected in one run drawn on top.

Used to produce independent visual evidence: the reviewer compares the printed
table with the parser's rectangle without any gold annotation in the image.

    python -m tools.render_detection_crops --run runs/<run> --page 13 \
        --out evidence/ds10_p13.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf

PADDING = 20.0
ZOOM = 2.2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--page", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--padding", type=float, default=PADDING)
    parser.add_argument("--zoom", type=float, default=ZOOM)
    parser.add_argument("--table-ids", default=None,
                        help="comma-separated table ids; default: all on page")
    args = parser.parse_args(argv)

    tables = json.loads((args.run / "tables.json").read_text(encoding="utf-8"))
    selected = [table for table in tables
                if table["page_number"] == args.page]
    if args.table_ids:
        wanted = {item.strip() for item in args.table_ids.split(",")}
        selected = [table for table in selected if table["table_id"] in wanted]
    if not selected:
        parser.error(f"no table on page {args.page}")
    boxes = [table["bbox"] for table in selected]
    clip = pymupdf.Rect(min(box[0] for box in boxes) - args.padding,
                        min(box[1] for box in boxes) - args.padding,
                        max(box[2] for box in boxes) + args.padding,
                        max(box[3] for box in boxes) + args.padding)

    document = pymupdf.open(str(args.run / "source.pdf"))
    try:
        page = document[args.page - 1]
        clip &= page.rect
        for table in selected:
            rect = pymupdf.Rect(*table["bbox"])
            page.draw_rect(rect, color=(0.0, 0.35, 0.85), width=1.2)
            page.insert_text((rect.x0 + 2, rect.y1 + 7),
                             table["table_id"], fontsize=6,
                             color=(0.0, 0.35, 0.85))
        pixmap = page.get_pixmap(clip=clip,
                                 matrix=pymupdf.Matrix(args.zoom, args.zoom))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        pixmap.save(str(args.out))
        print(f"{args.out}: {pixmap.width}x{pixmap.height} "
              f"tables={[table['table_id'] for table in selected]}")
    finally:
        document.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
