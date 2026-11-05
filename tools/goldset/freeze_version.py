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

REQUIRED_FILES = ["spec.yaml", "gold_table_set.jsonl", "manifest.json"]
OPTIONAL_FILES = ["PARAMS_FROZEN.json", "independent_review.json", "review_record.md"]


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


def freeze(version: str | None = None, gold_dir: Path = GOLD_DIR) -> Path:
    gold_dir = Path(gold_dir).resolve()
    spec_path = gold_dir / "spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    version = version or spec.get("annotation_version")
    if not version:
        raise ValueError(f"annotation_version is missing from {spec_path}")
    versions_dir = gold_dir / "versions"
    destination = versions_dir / version
    if destination.exists():
        raise FileExistsError(f"gold version already frozen: {destination}")

    files = list(REQUIRED_FILES)
    files += [name for name in OPTIONAL_FILES if (gold_dir / name).exists()]
    hashes = {}
    for name in files:
        source = gold_dir / name
        if not source.exists():
            raise FileNotFoundError(f"cannot freeze missing gold file: {source}")
        hashes[name] = _sha256(source)
    record = {
        "annotation_version": version,
        "gold_dir": gold_dir.relative_to(ROOT).as_posix(),
        "frozen_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_commit": _source_commit(),
        "files": hashes,
        "note": "Immutable snapshot; corrections require a new annotation_version.",
    }
    destination.mkdir(parents=True)
    try:
        for name in files:
            shutil.copyfile(gold_dir / name, destination / name)
        (destination / "VERSION.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8", newline="\n",
        )
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="defaults to annotation_version in spec.yaml")
    parser.add_argument("--gold-dir", type=Path, default=GOLD_DIR,
                        help="directory holding spec.yaml and the generated files")
    args = parser.parse_args()
    try:
        destination = freeze(args.version, args.gold_dir)
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        print(f"freeze failed: {error}")
        return 1
    print(f"frozen: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
