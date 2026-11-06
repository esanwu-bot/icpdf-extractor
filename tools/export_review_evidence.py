"""Export review artifacts for Phase 1.4 S1 (components, grids, eval diff).

Read-only: parses a PDF for physical components, reads a run's tables.json for
one logical table, and compares two evaluate.py JSON files item by item.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pymupdf as fitz

from icpdf.parser.layout import rule_components
from icpdf.parser.pdf_loader import load_pdf
from icpdf.parser.text_blocks import extract_text_blocks


def _write(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                    encoding="utf-8")


def export_components(pdf: Path, page_number: int, out: Path) -> None:
    loaded = load_pdf(pdf)
    with fitz.open(str(pdf)) as doc:
        page = doc[page_number - 1]
        geometry = loaded.geometries[page_number - 1]
        components = sorted(rule_components(page, geometry,
                                            page_number=page_number),
                            key=lambda component: component.bbox[1])
        blocks = extract_text_blocks(page, page_number, geometry)

    entries = []
    for component in components:
        entries.append({
            "component_id": component.component_id,
            "bbox": [round(value, 2) for value in component.bbox],
            "horizontal_rules": len(component.horizontal),
            "vertical_rules": len(component.vertical),
            "column_xs": [round(value, 2) for value in sorted(
                {segment.c for segment in component.vertical})],
            "primitive_count": len(component.primitives),
            "primitive_kinds": sorted({item.kind for item in component.primitives}),
            "primitive_indices": list(component.primitive_indices),
        })

    gaps = []
    for upper, lower in zip(components, components[1:]):
        labels = []
        for block in blocks:
            for span in block.spans:
                if not span.text.strip():
                    continue
                if not (upper.bbox[3] - 1.0 <= span.bbox[1]
                        and span.bbox[3] <= lower.bbox[1] + 1.0):
                    continue
                if not (min(upper.bbox[0], lower.bbox[0])
                        <= (span.bbox[0] + span.bbox[2]) / 2.0
                        <= max(upper.bbox[2], lower.bbox[2])):
                    continue
                labels.append({"text": span.text.strip(),
                               "size": span.size,
                               "bbox": [round(value, 2) for value in span.bbox]})
        gaps.append({
            "upper": upper.component_id,
            "lower": lower.component_id,
            "height_pt": round(lower.bbox[1] - upper.bbox[3], 2),
            "labels": labels,
        })

    _write(out, {"pdf": str(pdf), "page": page_number,
                 "components": entries, "gaps": gaps})


def export_grid(run: Path, page_number: int, table_id: str, out: Path) -> None:
    tables = json.loads((run / "tables.json").read_text(encoding="utf-8"))
    table = next(item for item in tables
                 if item["page_number"] == page_number
                 and item["table_id"] == table_id)
    rows = []
    column_xs = set()
    for row_index, row in enumerate(table["rows"]):
        cells = []
        for cell in row["cells"]:
            column_xs.update((round(cell["bbox"][0], 2),
                              round(cell["bbox"][2], 2)))
            cells.append({
                "cell_id": cell["cell_id"],
                "column_id": cell["column_id"],
                "bbox": [round(value, 2) for value in cell["bbox"]],
                "text": cell["text"],
            })
        rows.append({
            "row_index": row_index,
            "row_id": row["row_id"],
            "bbox": [round(value, 2) for value in row["bbox"]],
            "cells": cells,
        })
    xs = sorted(column_xs)
    full_width = [
        row["row_index"] for row in rows
        if any(abs(cell["bbox"][0] - table["bbox"][0]) <= 0.5
               and abs(cell["bbox"][2] - table["bbox"][2]) <= 0.5
               for cell in row["cells"])
    ]
    _write(out, {
        "run": run.name,
        "table_id": table_id,
        "page": page_number,
        "bbox": [round(value, 2) for value in table["bbox"]],
        "header_rows": table["header_rows"],
        "headers": table["headers"],
        "row_count": len(rows),
        "column_count": len(xs) - 1,
        "column_xs": xs,
        "full_width_rows_detected": full_width,
        "region_components": table.get("region_components"),
        "boundary_source": table.get("boundary_source"),
        "merge_evidence": table.get("merge_evidence"),
        "rows": rows,
    })


def export_diff(before: Path, after: Path, out: Path) -> None:
    old = json.loads(before.read_text(encoding="utf-8"))
    new = json.loads(after.read_text(encoding="utf-8"))
    old_items = {item["item_id"]: item for item in old["tables"]}
    new_items = {item["item_id"]: item for item in new["tables"]}
    fields = ("matched", "iou", "pred_rows", "pred_columns",
              "pred_table_type", "gold_rows", "gold_columns")
    entries = []
    for item_id in sorted(old_items):
        before_item = old_items[item_id]
        after_item = new_items[item_id]
        row = {"item_id": item_id, "page": before_item["page"]}
        changed = False
        for field in fields:
            before_value = before_item.get(field)
            after_value = after_item.get(field)
            row[field] = {"before": before_value, "after": after_value}
            if before_value != after_value:
                changed = True
        row["changed"] = changed
        entries.append(row)
    _write(out, {
        "before_label": old["label"],
        "after_label": new["label"],
        "overall_before": old["overall"],
        "overall_after": new["overall"],
        "changed_items": [item["item_id"] for item in entries if item["changed"]],
        "items": entries,
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    components = sub.add_parser("components")
    components.add_argument("--pdf", required=True)
    components.add_argument("--page", type=int, required=True)
    components.add_argument("--out", required=True)

    grid = sub.add_parser("grid")
    grid.add_argument("--run", required=True)
    grid.add_argument("--page", type=int, required=True)
    grid.add_argument("--table-id", required=True)
    grid.add_argument("--out", required=True)

    diff = sub.add_parser("diff")
    diff.add_argument("--before", required=True)
    diff.add_argument("--after", required=True)
    diff.add_argument("--out", required=True)

    args = parser.parse_args()
    if args.command == "components":
        export_components(Path(args.pdf), args.page, Path(args.out))
    elif args.command == "grid":
        export_grid(Path(args.run), args.page, args.table_id, Path(args.out))
    else:
        export_diff(Path(args.before), Path(args.after), Path(args.out))


if __name__ == "__main__":
    main()
