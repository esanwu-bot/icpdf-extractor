"""Developer helper: list rule components on selected pages.

Usage:
    python -m tools.goldset.inspect_components <pdf> <page> [<page> ...]
"""

from __future__ import annotations

import sys

import pymupdf

from tools.goldset.rules import rule_components


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    pdf = argv[1]
    pages = [int(p) for p in argv[2:]]
    with pymupdf.open(pdf) as doc:
        for page_number in pages:
            page = doc[page_number - 1]
            components = rule_components(page)
            print(f"--- page {page_number}: {len(components)} components")
            for index, component in enumerate(components):
                bbox = tuple(round(v, 1) for v in component.bbox)
                print(f"  [{index}] bbox={bbox} h={len(component.horizontal)} v={len(component.vertical)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
