"""Render a before/after delta between two evaluator JSON reports.

Usage:
    python -m tools.goldset.compare \
        --before gold/baseline_report.json \
        --after gold/after_report.json \
        --out gold/comparison.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

OVERALL = [
    ("Gold tables", "tables", "int"),
    ("TP", "tp", "int"),
    ("FP", "fp", "int"),
    ("FN", "fn", "int"),
    ("Precision", "precision", "f4"),
    ("Recall", "recall", "f4"),
    ("F1", "f1", "f4"),
    ("Negative FP", "negative_fp", "int"),
    ("Out-of-scope predictions", "out_of_scope_predictions", "int"),
]

STRUCTURE = [
    ("Matched tables", "matched", "int"),
    ("Row count exact", "row_count_exact", "int"),
    ("Column count exact", "column_count_exact", "int"),
    ("Row and column exact", "row_and_column_exact", "int"),
    ("Cell-text F1", "cell_text_f1", "f4"),
    ("Header comparable tables", "header_comparable_tables", "int"),
    ("Header comparable columns", "header_comparable_columns", "int"),
    ("Header column accuracy", "header_column_accuracy", "f4"),
    ("Header column accuracy (strict spacing)", "header_column_accuracy_strict", "f4"),
    ("Header row-depth exact", "header_row_depth_exact", "int"),
    ("Header tables exact", "header_tables_exact", "int"),
    ("Header multi-layer exact", "header_multilayer_exact", "int"),
    ("Header cell-text F1", "header_cell_text_f1", "f4"),
    ("Column-role accuracy", "column_role_accuracy", "f4"),
    ("Column-role columns", "column_role_columns", "int"),
    ("Column-role tables exact", "column_role_tables_exact", "int"),
    ("Table-type accuracy", "table_type_accuracy", "f4"),
]

DENOMINATORS = [
    ("Detection precision", "TP / (TP + in-scope FP)"),
    ("Detection recall", "TP / (TP + FN); every accepted gold table counts"),
    ("Row count exact", "matched tables whose predicted row count equals gold"),
    ("Column count exact", "matched tables whose predicted column count equals gold"),
    ("Cell-text F1", "cell multiset over the cells of matched tables"),
    ("Header column accuracy", "columns with equal compact label / labeled gold columns of comparable tables"),
    ("Header column accuracy (strict)", "same denominator, exact spacing"),
    ("Header row depth", "matched tables with equal header_rows"),
    ("Header tables exact", "comparable tables with every labeled column exact"),
    ("Header multi-layer", "matched tables whose gold header_rows >= 2"),
    ("Header cell-text F1", "labeled header cells of comparable tables"),
    ("Column role", "columns with equal coarse role / comparable columns"),
    ("Table type", "matched tables with equal table_type"),
]


def _fmt(value, kind: str) -> str:
    if value is None:
        return "—"
    if kind == "f4":
        return f"{float(value):.4f}"
    return str(value)


def _delta(before, after, kind: str) -> str:
    if before is None or after is None:
        return "—"
    diff = float(after) - float(before)
    if kind == "f4":
        return f"{diff:+.4f}"
    return f"{int(diff):+d}"


def _section(title: str, rows, before: dict, after: dict) -> list[str]:
    lines = [f"## {title}", "", "| Metric | Baseline | After | Delta |", "| --- | --- | --- | --- |"]
    for label, key, kind in rows:
        b, a = before.get(key), after.get(key)
        lines.append(f"| {label} | {_fmt(b, kind)} | {_fmt(a, kind)} | {_delta(b, a, kind)} |")
    return lines + [""]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    before = json.loads(Path(args.before).read_text(encoding="utf-8"))
    after = json.loads(Path(args.after).read_text(encoding="utf-8"))

    lines = [
        "# Phase 1.2 before/after on the same Gold Set",
        "",
        f"- Before: `{before['label']}` (parser committed as `phase1.1-baseline`)",
        f"- After: `{after['label']}` ({after['generated_at']})",
        f"- Gold annotation: `{after['annotation_version']}`",
        "",
    ]
    lines += _section("Table detection", OVERALL, before["overall"], after["overall"])
    lines += _section("Structure on matched tables", STRUCTURE,
                      before.get("structure", {}), after.get("structure", {}))

    lines += ["## Per PDF (table detection)", "",
              "| PDF | Baseline P / R / F1 | After P / R / F1 |",
              "| --- | --- | --- |"]
    before_pdf = before.get("per_pdf", {})
    for pdf_id, row in after.get("per_pdf", {}).items():
        old = before_pdf.get(pdf_id, {})
        lines.append(
            f"| {pdf_id} | {old.get('precision', 0):.4f} / "
            f"{old.get('recall', 0):.4f} / {old.get('f1', 0):.4f} | "
            f"{row['precision']:.4f} / {row['recall']:.4f} / {row['f1']:.4f} |")
    lines += [""]

    lines += ["## Fragmentation", "",
              "| Metric | Baseline | After |",
              "| --- | --- | --- |",
              f"| Mean predictions overlapping one gold table | "
              f"{before['fragmentation']['mean_overlapping_predictions']} | "
              f"{after['fragmentation']['mean_overlapping_predictions']} |",
              f"| Maximum overlapping predictions | "
              f"{before['fragmentation']['max_overlapping_predictions']} | "
              f"{after['fragmentation']['max_overlapping_predictions']} |",
              ""]

    lines += ["## Negative samples", "",
              "| Negative kind | Baseline FP | After FP |",
              "| --- | --- | --- |"]
    before_neg = before.get("negatives", {}).get("by_kind", {})
    after_neg = after.get("negatives", {}).get("by_kind", {})
    for kind in sorted(set(before_neg) | set(after_neg)):
        lines.append(f"| {kind} | {before_neg.get(kind, {}).get('fp', 0)} | "
                     f"{after_neg.get(kind, {}).get('fp', 0)} |")
    lines += [""]

    bs = before.get("structure", {})
    as_ = after.get("structure", {})
    lines += ["## Metric denominators", "",
              "| Metric family | Denominator |", "| --- | --- |"]
    lines += [f"| {label} | {text} |" for label, text in DENOMINATORS]
    lines += [""]

    notes = [
        "## Notes",
        "",
        f"- Cell-text F1 is computed over matched tables ({bs.get('matched')} baseline, "
        f"{as_.get('matched')} after), so those values are not directly comparable.",
        f"- Header column attribution and column-role accuracy are scored only on tables "
        f"whose predicted column count equals gold: {bs.get('header_comparable_tables')} "
        f"table(s) / {bs.get('header_comparable_columns')} column(s) baseline versus "
        f"{as_.get('header_comparable_tables')} tables / {as_.get('header_comparable_columns')} "
        "columns after. The baseline had no header model, so its accuracy values rest on "
        "a much smaller denominator and must be read with those counts.",
        "- Table-type accuracy uses matched tables as the denominator; the per-class "
        "confusion matrix is in `gold/after_report.md`.",
        "",
    ]
    lines += notes

    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
