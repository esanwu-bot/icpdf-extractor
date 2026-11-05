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
    ("Header column accuracy", "header_column_accuracy", "f4"),
    ("Header tables exact", "header_tables_exact", "int"),
    ("Column-role accuracy", "column_role_accuracy", "f4"),
    ("Column-role tables exact", "column_role_tables_exact", "int"),
    ("Table-type accuracy", "table_type_accuracy", "f4"),
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

    notes = [
        "## Notes",
        "",
        "- Cell-text F1 is computed only over matched tables, so the baseline value",
        "  (16 matched) and the after value (39 matched) are not directly comparable;",
        "  all other structure metrics share the same denominator.",
        "- Header/role metrics count a table only when the predicted column count",
        "  equals the gold column count, matching `gold/README.md`.",
        "",
    ]
    lines += notes

    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
