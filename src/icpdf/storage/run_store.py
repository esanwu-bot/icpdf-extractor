"""Run directory management. A run is immutable; reruns get a new run_id."""

from __future__ import annotations

import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path

from icpdf.storage.artifact_store import sha256_file, write_json


class RunStore:
    def __init__(self, root: Path, run_id: str) -> None:
        self.root = Path(root)
        self.run_id = run_id
        self.dir = self.root / run_id
        self._artifacts: list[dict] = []

    @classmethod
    def create(cls, root: str | Path, run_id: str | None = None) -> "RunStore":
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        if run_id is None:
            run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)
        run = cls(root, run_id)
        if run.dir.exists():
            raise FileExistsError(f"run already exists, refusing to overwrite: {run.dir}")
        run.dir.mkdir(parents=True)
        return run

    def copy_source(self, pdf_path: str | Path) -> str:
        src = Path(pdf_path)
        dest = self.dir / "source.pdf"
        shutil.copyfile(src, dest)
        return sha256_file(dest)

    def write_json(self, name: str, data: dict | list) -> dict:
        entry = write_json(self.dir / name, data)
        self._artifacts.append({"name": name, "sha256": entry["sha256"],
                                "bytes": entry["bytes"]})
        return entry

    def artifact_entries(self) -> list[dict]:
        return list(self._artifacts)

    def write_manifest(self, payload: dict) -> dict:
        locked = {**payload, "artifacts": self.artifact_entries()}
        return write_json(self.dir / "run_manifest.json", locked)
