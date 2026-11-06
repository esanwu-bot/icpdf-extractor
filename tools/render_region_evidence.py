"""Render S1 review images: physical components vs region, and the cell grid.

Both modes are read-only and never write into a run directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf as fitz

from icpdf.parser.layout import rule_components
from icpdf.parser.pdf_loader import load_pdf

_COLORS = [
    (0.85, 0.20, 0.20), (0.10, 0.55, 0.25), (0.75, 0.40, 0.10),
    (0.45, 0.20, 0.70), (0.45, 0.30, 0.10), (0.80, 0.20, 0.60),
]
_BLUE = (0.0, 0.15, 0.85)


def _render_components(pdf: Path, page_number: int, run: Path | None,
                       table_id: str | None, out: Path, padding: float,
                       zoom: float) -> None:
    loaded = load_pdf(pdf)
    with fitz.open(str(pdf)) as doc:
        page = doc[page_number - 1]
        geometry = loaded.geometries[page_number - 1]
        components = sorted(rule_components(page, geometry,
                                            page_number=page_number),
                            key=lambda component: component.bbox[1])
        tables = []
        if run is not None:
            all_tables = json.loads((run / "tables.json").read_text(
                encoding="utf-8"))
            tables = [table for table in all_tables
                      if table["page_number"] == page_number
                      and (table_id is None or table["table_id"] == table_id)]
        boxes = [component.bbox for component in components]
        boxes += [table["bbox"] for table in tables]
        if not boxes:
            raise SystemExit("nothing to draw on this page")
        clip = fitz.Rect(min(box[0] for box in boxes) - padding,
                         min(box[1] for box in boxes) - padding,
                         max(box[2] for box in boxes) + padding,
                         max(box[3] for box in boxes) + padding)

        for component in components:
            color = _COLORS[component.component_id % len(_COLORS)]
            rect = fitz.Rect(component.bbox)
            page.draw_rect(rect, color=color, width=1.2)
            label_x = rect.x0 - 30
            label_y = (rect.y0 + rect.y1) / 2.0 + 2.0
            page.draw_rect(fitz.Rect(label_x - 1, label_y - 6,
                                     label_x + 16, label_y + 1),
                           color=None, fill=(1.0, 1.0, 1.0), width=0)
            page.insert_text((label_x, label_y),
                             f"C{component.component_id}", fontsize=6,
                             color=color)
        for table in tables:
            rect = fitz.Rect(table["bbox"])
            page.draw_rect(rect, color=_BLUE, width=2.0)
            page.insert_text((rect.x0 + 2, rect.y1 + 10),
                             f"REGION {table['table_id']}", fontsize=7,
                             color=_BLUE)

        pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip)
        out.parent.mkdir(parents=True, exist_ok=True)
        pixmap.save(str(out))


def _render_grid(run: Path, page_number: int, table_id: str, out: Path,
                 padding: float, zoom: float, labels: str) -> None:
    doc = fitz.open(str(run / "source.pdf"))
    try:
        page = doc[page_number - 1]
        tables = json.loads((run / "tables.json").read_text(encoding="utf-8"))
        table = next(item for item in tables
                     if item["page_number"] == page_number
                     and item["table_id"] == table_id)
        bbox = table["bbox"]
        clip = fitz.Rect(bbox[0] - padding, bbox[1] - padding,
                         bbox[2] + padding, bbox[3] + padding)
        page.draw_rect(fitz.Rect(bbox), color=_BLUE, width=1.2)

        xs = sorted({round(cell["bbox"][0], 2) for row in table["rows"]
                     for cell in row["cells"]}
                    | {round(cell["bbox"][2], 2) for row in table["rows"]
                       for cell in row["cells"]})
        for column, x in enumerate(xs):
            page.draw_line(fitz.Point(x, bbox[1]), fitz.Point(x, bbox[3]),
                           color=(0.0, 0.55, 0.55), width=0.4,
                           dashes="[1 1] 0")
            page.insert_text((x + 1.5, bbox[1] - 2), str(column),
                             fontsize=4, color=(0.0, 0.45, 0.45))

        for row_index, row in enumerate(table["rows"]):
            y = row["bbox"][1]
            page.draw_line(fitz.Point(bbox[0], y), fitz.Point(bbox[2], y),
                           color=(0.0, 0.55, 0.55), width=0.4,
                           dashes="[1 1] 0")
            page.insert_text((bbox[0] - 13, y + 4), f"r{row_index}",
                             fontsize=3.6, color=(0.0, 0.45, 0.45))
            if labels == "cell":
                for cell in row["cells"]:
                    cell_box = cell["bbox"]
                    page.insert_text((cell_box[0] + 1, cell_box[1] + 4),
                                     f"c{cell['column_id']}", fontsize=3.4,
                                     color=(0.55, 0.55, 0.55))

        pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip)
        out.parent.mkdir(parents=True, exist_ok=True)
        pixmap.save(str(out))
    finally:
        doc.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    components = sub.add_parser("components")
    components.add_argument("--pdf", required=True)
    components.add_argument("--page", type=int, required=True)
    components.add_argument("--run")
    components.add_argument("--table-id")
    components.add_argument("--out", required=True)
    components.add_argument("--padding", type=float, default=20.0)
    components.add_argument("--zoom", type=float, default=3.0)

    grid = sub.add_parser("grid")
    grid.add_argument("--run", required=True)
    grid.add_argument("--page", type=int, required=True)
    grid.add_argument("--table-id", required=True)
    grid.add_argument("--out", required=True)
    grid.add_argument("--padding", type=float, default=10.0)
    grid.add_argument("--zoom", type=float, default=3.0)
    grid.add_argument("--labels", choices=("none", "row", "cell"),
                      default="cell")

    args = parser.parse_args()
    if args.command == "components":
        _render_components(Path(args.pdf), args.page,
                           Path(args.run) if args.run else None,
                           args.table_id, Path(args.out), args.padding,
                           args.zoom)
    else:
        _render_grid(Path(args.run), args.page, args.table_id, Path(args.out),
                     args.padding, args.zoom, args.labels)


if __name__ == "__main__":
    main()
