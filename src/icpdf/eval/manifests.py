"""Read-only identity checks for the Gold v1, Gold v2 and S2b manifests.

Implements §12.1 D: ids are indexed globally, positive identity is
``(pdf_sha256, page, table_index)`` parsed from ``-Pnn-Tnn``, and the only
permitted cross-set physical reuse is the declared v2-to-s2b derivation.
Nothing here writes, reorders or normalizes a manifest.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from icpdf.eval.jsonio import read_manifest_rows

_ITEM = re.compile(r"-P(\d+)-T(\d+)$")
_SET_NAMES = ("v1", "v2", "s2b")


@dataclass(frozen=True)
class ManifestSpec:
    name: str
    path: Path
    expected_counts: tuple[int, int] | None = None
    required: bool = True


@dataclass(frozen=True)
class ManifestFinding:
    code: str
    detail: str
    manifests: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {"code": self.code, "detail": self.detail,
                "manifests": list(self.manifests)}


@dataclass(frozen=True)
class _Item:
    manifest: str
    line: int
    item_id: str | None
    positive: bool
    triple: tuple[str, int, int] | None
    derived_from: str | None


def declared_counts(path: Path) -> dict | None:
    """Read the sibling ``manifest.json`` counts, if present."""
    meta = path.parent / "manifest.json"
    if not meta.is_file():
        return None
    document = json.loads(meta.read_text(encoding="utf-8"))
    counts = document.get("counts") if isinstance(document, dict) else None
    return counts if isinstance(counts, dict) else None


def _read_items(spec: ManifestSpec, findings: list[ManifestFinding]) -> list[_Item]:
    items: list[_Item] = []
    for line, record in read_manifest_rows(spec.path):
        if not isinstance(record, dict):
            findings.append(ManifestFinding(
                "eval_manifest_identity_ambiguous",
                f"{spec.name} line {line}: item is not a JSON object",
                (spec.name,)))
            continue
        item_id = record.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            findings.append(ManifestFinding(
                "eval_manifest_identity_ambiguous",
                f"{spec.name} line {line}: missing item_id", (spec.name,)))
            item_id = None
        positive = record.get("kind") != "negative"
        triple = None
        if positive:
            sha = record.get("pdf_sha256")
            page = record.get("page")
            match = _ITEM.search(item_id) if item_id else None
            if not isinstance(sha, str) or not sha:
                findings.append(ManifestFinding(
                    "eval_manifest_identity_ambiguous",
                    f"{spec.name} line {line}: positive has no pdf_sha256",
                    (spec.name,)))
            elif type(page) is not int:
                findings.append(ManifestFinding(
                    "eval_manifest_identity_ambiguous",
                    f"{spec.name} line {line}: positive has no integer page",
                    (spec.name,)))
            elif match is None:
                findings.append(ManifestFinding(
                    "eval_manifest_identity_ambiguous",
                    f"{spec.name} line {line}: item_id has no -Pnn-Tnn suffix",
                    (spec.name,)))
            elif int(match.group(1)) != page:
                findings.append(ManifestFinding(
                    "eval_manifest_identity_ambiguous",
                    f"{spec.name} line {line}: page {page} contradicts "
                    f"the -P segment of {item_id}", (spec.name,)))
            else:
                triple = (sha, page, int(match.group(2)))
        derived = record.get("derived_from_item_id")
        if spec.name == "s2b" and derived is not None and (
                not isinstance(derived, str) or not derived):
            findings.append(ManifestFinding(
                "eval_manifest_derived_identity_mismatch",
                f"{spec.name} line {line}: derived_from_item_id is not a "
                "non-empty string", (spec.name,)))
            derived = None
        items.append(_Item(
            manifest=spec.name, line=line, item_id=item_id, positive=positive,
            triple=triple,
            derived_from=derived if isinstance(derived, str) and derived else None))
    return items


def _check_counts(spec: ManifestSpec, items: Sequence[_Item],
                  findings: list[ManifestFinding]) -> dict:
    positives = sum(1 for item in items if item.positive)
    negatives = sum(1 for item in items if not item.positive)
    counts = {"positives": positives, "negatives": negatives}
    declared = declared_counts(spec.path)
    if declared is not None:
        declared_pos = declared.get("positives", declared.get("tables"))
        declared_neg = declared.get("negatives")
        if declared_pos is not None and declared_pos != positives:
            findings.append(ManifestFinding(
                "eval_manifest_count_mismatch",
                f"{spec.name}: declared {declared_pos} positives, "
                f"enumerated {positives}", (spec.name,)))
        if declared_neg is not None and declared_neg != negatives:
            findings.append(ManifestFinding(
                "eval_manifest_count_mismatch",
                f"{spec.name}: declared {declared_neg} negatives, "
                f"enumerated {negatives}", (spec.name,)))
    if spec.expected_counts is not None and \
            spec.expected_counts != (positives, negatives):
        findings.append(ManifestFinding(
            "eval_manifest_count_mismatch",
            f"{spec.name}: expected {spec.expected_counts}, "
            f"enumerated {(positives, negatives)}", (spec.name,)))
    return counts


def check_eval_manifests(specs: Sequence[ManifestSpec]) -> dict:
    """Check the manifests read-only; report per-set PASS/SKIPPED/FAIL.

    A missing optional manifest is ``skipped`` and can never produce a PASS for
    the run.  Checks that relate two sets are only meaningful for the sets that
    are actually present; the report keeps that distinction instead of
    collapsing it into a single ``ok`` flag.
    """
    names = [spec.name for spec in specs]
    if len(set(names)) != len(names):
        raise ValueError("manifest names must be unique")
    for name in names:
        if name not in _SET_NAMES:
            raise ValueError(f"unknown manifest name: {name}")
    findings: list[ManifestFinding] = []
    statuses: dict[str, str] = {}
    skipped: list[str] = []
    present: list[ManifestSpec] = []
    for spec in specs:
        if spec.path.is_file():
            statuses[spec.name] = "pass"
            present.append(spec)
        elif spec.required:
            findings.append(ManifestFinding(
                "eval_manifest_missing",
                f"{spec.name}: manifest not found: {spec.path}", (spec.name,)))
            statuses[spec.name] = "fail"
        else:
            statuses[spec.name] = "skipped"
            skipped.append(spec.name)
    present_names = [spec.name for spec in present]
    items_by_set = {spec.name: _read_items(spec, findings) for spec in present}

    by_id: dict[str, list[_Item]] = {}
    for name in present_names:
        for item in items_by_set[name]:
            if item.item_id is not None:
                by_id.setdefault(item.item_id, []).append(item)

    for item_id, occurrences in by_id.items():
        if len(occurrences) < 2:
            continue
        for index, item in enumerate(occurrences):
            for prior in occurrences[:index]:
                if prior.manifest == item.manifest:
                    findings.append(ManifestFinding(
                        "eval_manifest_duplicate_item_id",
                        f"{item.manifest}: {item_id} occurs at lines "
                        f"{prior.line} and {item.line}", (item.manifest,)))
                else:
                    findings.append(ManifestFinding(
                        "eval_manifest_item_id_collision",
                        f"{item_id} occurs in {prior.manifest} line {prior.line} "
                        f"and {item.manifest} line {item.line}",
                        (prior.manifest, item.manifest)))
                    if prior.positive != item.positive:
                        findings.append(ManifestFinding(
                            "eval_manifest_polarity_conflict",
                            f"{item_id} is positive in one manifest and negative "
                            f"in another ({prior.manifest} line {prior.line}, "
                            f"{item.manifest} line {item.line})",
                            (prior.manifest, item.manifest)))

    triples: dict[str, dict[tuple[str, int, int], _Item]] = {}
    for name in present_names:
        seen: dict[tuple[str, int, int], _Item] = {}
        for item in items_by_set[name]:
            if item.triple is None:
                continue
            prior = seen.get(item.triple)
            if prior is not None:
                findings.append(ManifestFinding(
                    "eval_manifest_identity_ambiguous",
                    f"{name}: {prior.item_id} and {item.item_id} share "
                    f"(sha256, page, table_index) {item.triple}", (name,)))
            else:
                seen[item.triple] = item
        triples[name] = seen

    v1_triples = triples.get("v1", {})
    v2_triples = triples.get("v2", {})
    s2b_triples = triples.get("s2b", {})
    for triple in sorted(set(v1_triples) & set(v2_triples)):
        findings.append(ManifestFinding(
            "eval_manifest_cross_manifest_identity_collision",
            f"v1 {v1_triples[triple].item_id} and v2 "
            f"{v2_triples[triple].item_id} share {triple}", ("v1", "v2")))
    for triple, item in s2b_triples.items():
        if triple in v1_triples:
            findings.append(ManifestFinding(
                "eval_manifest_s2b_identity_collision",
                f"s2b {item.item_id} shares {triple} with v1 "
                f"{v1_triples[triple].item_id}", ("s2b", "v1")))
        target = v2_triples.get(triple)
        if target is not None and item.derived_from != target.item_id:
            findings.append(ManifestFinding(
                "eval_manifest_s2b_identity_collision",
                f"s2b {item.item_id} shares {triple} with v2 "
                f"{target.item_id} without naming it as derived_from_item_id",
                ("s2b", "v2")))

    v2_by_id: dict[str, list[_Item]] = {}
    for item in items_by_set.get("v2", []):
        if item.item_id is not None:
            v2_by_id.setdefault(item.item_id, []).append(item)
    sources: dict[str, _Item] = {}
    for item in items_by_set.get("s2b", []):
        if item.derived_from is None:
            continue
        if not item.positive:
            findings.append(ManifestFinding(
                "eval_manifest_derived_identity_mismatch",
                f"s2b {item.item_id} is a negative with derived_from_item_id",
                ("s2b",)))
            continue
        occurrences = v2_by_id.get(item.derived_from, [])
        if len(occurrences) != 1:
            findings.append(ManifestFinding(
                "eval_manifest_derived_identity_mismatch",
                f"s2b {item.item_id} derived_from_item_id "
                f"{item.derived_from} resolves to {len(occurrences)} v2 items, "
                "not one", ("s2b", "v2")))
            continue
        source = occurrences[0]
        if not source.positive:
            findings.append(ManifestFinding(
                "eval_manifest_derived_identity_mismatch",
                f"s2b {item.item_id} derives from v2 negative "
                f"{source.item_id}", ("s2b", "v2")))
        if item.item_id == item.derived_from:
            findings.append(ManifestFinding(
                "eval_manifest_derived_identity_mismatch",
                f"s2b item_id {item.item_id} equals its derived_from_item_id",
                ("s2b",)))
        if item.triple is None or source.triple is None:
            findings.append(ManifestFinding(
                "eval_manifest_derived_identity_mismatch",
                f"s2b {item.item_id} or its v2 source has no parsable identity",
                ("s2b", "v2")))
        elif item.triple != source.triple:
            findings.append(ManifestFinding(
                "eval_manifest_derived_identity_mismatch",
                f"s2b {item.item_id} identity {item.triple} differs from "
                f"source {source.item_id} identity {source.triple}",
                ("s2b", "v2")))
        prior = sources.get(item.derived_from)
        if prior is not None:
            findings.append(ManifestFinding(
                "eval_manifest_derived_identity_mismatch",
                f"derived_from_item_id {item.derived_from} is declared by both "
                f"{prior.item_id} and {item.item_id}", ("s2b", "v2")))
        else:
            sources[item.derived_from] = item

    counts = {spec.name: _check_counts(spec, items_by_set[spec.name], findings)
              for spec in present}
    for finding in findings:
        for name in finding.manifests:
            # A skipped set did not participate, so a finding elsewhere must
            # never turn SKIPPED into FAIL.
            if statuses.get(name) == "pass":
                statuses[name] = "fail"
    status = ("fail" if any(value == "fail" for value in statuses.values())
              else "partial" if skipped else "pass")
    return {
        "ok": status == "pass",
        "status": status,
        "sets": {
            name: {
                "status": statuses[name],
                "counts": counts.get(name),
                "findings": sum(1 for finding in findings
                                if name in finding.manifests),
            }
            for name in names
        },
        "skipped": skipped,
        "findings": [finding.as_dict() for finding in findings],
        "counts": counts,
    }
