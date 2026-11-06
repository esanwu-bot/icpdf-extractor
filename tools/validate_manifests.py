#!/usr/bin/env python3
"""Read-only check of the Gold v1/v2 and S2b evaluation manifests (§12.1 D).

Each set is reported as ``PASS``, ``SKIPPED`` or ``FAIL``.  A missing S2b
manifest is skipped, never silently treated as passing; in that state the
overall result is ``PARTIAL`` and cross-set derivation is not claimed.

Usage:
    python tools/validate_manifests.py [--s2b PATH] [--json]

Exit status: 0 all sets pass, 1 any finding, 3 required sets pass but at least
one optional set was skipped.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from icpdf.eval.manifests import ManifestSpec, check_eval_manifests  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v1", type=Path,
                        default=ROOT / "gold" / "gold_table_set.jsonl")
    parser.add_argument("--v2", type=Path, default=(
        ROOT / "gold" / "generalization" / "gold_table_set.jsonl"))
    parser.add_argument("--s2b", type=Path, default=None,
                        help="defaults to gold/s2b/gold_table_set.jsonl")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    known = (ROOT / "gold" / "gold_table_set.jsonl",
             ROOT / "gold" / "generalization" / "gold_table_set.jsonl")
    s2b_path = args.s2b or ROOT / "gold" / "s2b" / "gold_table_set.jsonl"
    specs = [
        ManifestSpec("v1", args.v1,
                     expected_counts=(46, 19) if args.v1 == known[0] else None),
        ManifestSpec("v2", args.v2,
                     expected_counts=(21, 8) if args.v2 == known[1] else None),
        # An S2b set the caller names explicitly is required; the default path
        # is optional so an absent S2b is reported rather than fatal.
        ManifestSpec("s2b", s2b_path, required=args.s2b is not None),
    ]

    report = check_eval_manifests(specs)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for finding in report["findings"]:
            print(f"{finding['code']}: {finding['detail']}")
        for name, entry in report["sets"].items():
            counts = entry["counts"]
            if entry["status"] == "skipped":
                print(f"{name}: SKIPPED (manifest absent; not verified)")
            elif counts is None:
                print(f"{name}: FAIL ({entry['findings']} finding(s))")
            else:
                suffix = (f"; {entry['findings']} finding(s)"
                          if entry["findings"] else "")
                print(f"{name}: {entry['status'].upper()} "
                      f"({counts['positives']} positives, "
                      f"{counts['negatives']} negatives{suffix})")
        print(f"overall: {report['status'].upper()}")
    if report["status"] == "fail":
        return 1
    return 3 if report["status"] == "partial" else 0


if __name__ == "__main__":
    raise SystemExit(main())
