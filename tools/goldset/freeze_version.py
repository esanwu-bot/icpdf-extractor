"""Freeze the current gold annotation as an immutable version snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = ROOT / "gold"
VERSIONS_DIR = GOLD_DIR / "versions"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_commit() -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT,
        capture_output=True, text=True, check=False,
    ).stdout.strip()
    return result or None


def freeze(version: str | None = None) -> Path:
    spec_path = GOLD_DIR / "spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    version = version or spec.get("annotation_version")
    if not version:
        raise ValueError("annotation_version is missing from gold/spec.yaml")
    destination = VERSIONS_DIR / version
    if destination.exists():
        raise FileExistsError(f"gold version already frozen: {destination}")

    files = ["spec.yaml", "gold_table_set.jsonl", "manifest.json"]
    hashes = {}
    for name in files:
        source = GOLD_DIR / name
        if not source.exists():
            raise FileNotFoundError(f"cannot freeze missing gold file: {source}")
        hashes[name] = _sha256(source)
    destination.mkdir(parents=True)
    for name in files:
        shutil.copyfile(GOLD_DIR / name, destination / name)
    record = {
        "annotation_version": version,
        "frozen_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_commit": _source_commit(),
        "files": hashes,
        "note": "Immutable snapshot; corrections require a new annotation_version.",
    }
    (destination / "VERSION.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="defaults to annotation_version in spec.yaml")
    args = parser.parse_args()
    try:
        destination = freeze(args.version)
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        print(f"freeze failed: {error}")
        return 1
    print(f"frozen: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
