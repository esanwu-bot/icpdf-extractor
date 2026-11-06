"""S2b-Schema: read-only identity and derivation checks for Gold manifests."""

from __future__ import annotations

import json
from pathlib import Path

from icpdf.eval.manifests import ManifestSpec, check_eval_manifests

ROOT = Path(__file__).resolve().parents[2]
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


def _write(path: Path, records: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records),
                    encoding="utf-8")
    return path


def _table(item_id: str, sha: str, page: int, **extra) -> dict:
    return {"item_id": item_id, "kind": "table", "pdf_sha256": sha,
            "page": page, **extra}


def _negative(item_id: str, sha: str, page: int) -> dict:
    return {"item_id": item_id, "kind": "negative", "pdf_sha256": sha,
            "page": page}


def _check(tmp_path: Path, sets: dict[str, list[dict]],
           expected: dict[str, tuple[int, int]] | None = None) -> dict:
    specs = []
    for name, records in sets.items():
        path = _write(tmp_path / f"{name}.jsonl", records)
        specs.append(ManifestSpec(name, path, (expected or {}).get(name)))
    return check_eval_manifests(specs)


def _codes(report: dict) -> set[str]:
    return {finding["code"] for finding in report["findings"]}


def test_frozen_regression_manifests_pass_with_expected_counts():
    report = check_eval_manifests([
        ManifestSpec("v1", ROOT / "gold" / "gold_table_set.jsonl", (46, 19)),
        ManifestSpec("v2", ROOT / "gold" / "generalization" / "gold_table_set.jsonl",
                     (21, 8)),
    ])
    assert report["ok"] is True
    assert report["counts"]["v1"] == {"positives": 46, "negatives": 19}
    assert report["counts"]["v2"] == {"positives": 21, "negatives": 8}


def test_declared_derivation_to_a_v2_positive_is_the_only_reuse(tmp_path):
    report = _check(tmp_path, {
        "v1": [_table("DOCA-P01-T01", SHA_A, 1)],
        "v2": [_table("DOCB-P01-T01", SHA_B, 1)],
        "s2b": [_table("DOCB2-P01-T01", SHA_B, 1,
                       derived_from_item_id="DOCB-P01-T01"),
                _table("DOCC-P01-T01", SHA_C, 1)],
    })
    assert report["ok"] is True


def test_non_derived_s2b_identity_collision_is_refused(tmp_path):
    report = _check(tmp_path, {
        "v2": [_table("DOCB-P01-T01", SHA_B, 1)],
        "s2b": [_table("DOCB2-P01-T01", SHA_B, 1)],
    })
    assert "eval_manifest_s2b_identity_collision" in _codes(report)


def test_derivation_cannot_bypass_a_v1_collision(tmp_path):
    report = _check(tmp_path, {
        "v1": [_table("DOCA-P01-T01", SHA_A, 1)],
        "v2": [_table("DOCB-P01-T01", SHA_B, 1)],
        "s2b": [_table("DOCC-P01-T01", SHA_A, 1,
                       derived_from_item_id="DOCB-P01-T01")],
    })
    codes = _codes(report)
    assert "eval_manifest_s2b_identity_collision" in codes
    assert "eval_manifest_derived_identity_mismatch" in codes


def test_cross_manifest_physical_identity_is_refused(tmp_path):
    report = _check(tmp_path, {
        "v1": [_table("DOCA-P01-T01", SHA_A, 1)],
        "v2": [_table("DOCB-P01-T01", SHA_A, 1)],
    })
    assert "eval_manifest_cross_manifest_identity_collision" in _codes(report)


def test_derivation_must_resolve_to_one_v2_positive_with_equal_identity(tmp_path):
    missing = _check(tmp_path / "a", {
        "v2": [_table("DOCB-P01-T01", SHA_B, 1)],
        "s2b": [_table("DOCB2-P01-T01", SHA_B, 1,
                       derived_from_item_id="MISSING-P01-T01")],
    })
    assert "eval_manifest_derived_identity_mismatch" in _codes(missing)

    negative = _check(tmp_path / "b", {
        "v2": [_negative("DOCB-P01-T01", SHA_B, 1)],
        "s2b": [_table("DOCB2-P01-T01", SHA_B, 1,
                       derived_from_item_id="DOCB-P01-T01")],
    })
    assert "eval_manifest_derived_identity_mismatch" in _codes(negative)

    different = _check(tmp_path / "c", {
        "v2": [_table("DOCB-P01-T01", SHA_B, 1)],
        "s2b": [_table("DOCB2-P02-T01", SHA_B, 2,
                       derived_from_item_id="DOCB-P01-T01")],
    })
    assert "eval_manifest_derived_identity_mismatch" in _codes(different)


def test_two_s2b_items_cannot_name_the_same_v2_source(tmp_path):
    report = _check(tmp_path, {
        "v2": [_table("DOCB-P01-T01", SHA_B, 1)],
        "s2b": [_table("DOCB2-P01-T01", SHA_B, 1,
                       derived_from_item_id="DOCB-P01-T01"),
                _table("DOCB3-P01-T01", SHA_B, 1,
                       derived_from_item_id="DOCB-P01-T01")],
    })
    assert "eval_manifest_derived_identity_mismatch" in _codes(report)


def test_duplicate_ids_report_both_locations(tmp_path):
    within = _check(tmp_path / "within", {
        "v1": [_table("DOCA-P01-T01", SHA_A, 1),
               _table("DOCA-P01-T01", SHA_A, 1)],
    })
    finding = next(item for item in within["findings"]
                   if item["code"] == "eval_manifest_duplicate_item_id")
    assert "lines 1 and 2" in finding["detail"]

    cross = _check(tmp_path / "cross", {
        "v1": [_table("DOCA-P01-T01", SHA_A, 1)],
        "v2": [_table("DOCA-P01-T01", SHA_B, 1)],
    })
    finding = next(item for item in cross["findings"]
                   if item["code"] == "eval_manifest_item_id_collision")
    assert "v1 line 1" in finding["detail"]
    assert "v2 line 1" in finding["detail"]


def test_polarity_conflict_is_reported(tmp_path):
    report = _check(tmp_path, {
        "v1": [_table("DOCA-P01-T01", SHA_A, 1)],
        "v2": [_negative("DOCA-P01-T01", SHA_A, 1)],
    })
    assert "eval_manifest_polarity_conflict" in _codes(report)


def test_within_set_identity_and_bad_suffix_are_ambiguous(tmp_path):
    shared = _check(tmp_path / "shared", {
        "v1": [_table("DOCA-P01-T01", SHA_A, 1),
               _table("DOCA-P02-T01", SHA_A, 2),
               _table("DOCA-P03-T01", SHA_A, 1)],
    })
    assert "eval_manifest_identity_ambiguous" in _codes(shared)

    bad_page = _check(tmp_path / "page", {
        "v1": [_table("DOCA-P04-T01", SHA_A, 5)],
    })
    assert "eval_manifest_identity_ambiguous" in _codes(bad_page)

    bad_suffix = _check(tmp_path / "suffix", {
        "v1": [_table("DOCA-P04", SHA_A, 4)],
    })
    assert "eval_manifest_identity_ambiguous" in _codes(bad_suffix)


def test_counts_are_checked_against_expected_and_declared(tmp_path):
    records = {"v1": [_table("DOCA-P01-T01", SHA_A, 1),
                      _negative("DOCA-N01", SHA_A, 1)]}
    report = _check(tmp_path / "expected", records,
                    expected={"v1": (1, 2)})
    assert "eval_manifest_count_mismatch" in _codes(report)

    declared = [{"item_id": "DOCA-P01-T01", "kind": "table",
                 "pdf_sha256": SHA_A, "page": 1}]
    path = _write(tmp_path / "declared" / "v1.jsonl", declared)
    (tmp_path / "declared" / "manifest.json").write_text(
        json.dumps({"counts": {"tables": 2, "negatives": 0}}),
        encoding="utf-8")
    report = check_eval_manifests([ManifestSpec("v1", path)])
    assert "eval_manifest_count_mismatch" in _codes(report)


def test_negative_on_the_same_page_is_not_an_identity_conflict(tmp_path):
    report = _check(tmp_path, {
        "v1": [_table("DOCA-P01-T01", SHA_A, 1),
               _negative("DOCA-N-P01", SHA_A, 1)],
    })
    assert report["ok"] is True
    assert report["status"] == "pass"


def test_all_present_sets_report_pass(tmp_path):
    report = _check(tmp_path, {
        "v1": [_table("DOCA-P01-T01", SHA_A, 1)],
        "v2": [_table("DOCB-P01-T01", SHA_B, 1)],
        "s2b": [_table("DOCB2-P01-T01", SHA_B, 1,
                       derived_from_item_id="DOCB-P01-T01")],
    })
    assert report["status"] == "pass"
    assert report["skipped"] == []
    assert {name: entry["status"] for name, entry in report["sets"].items()} == {
        "v1": "pass", "v2": "pass", "s2b": "pass"}


def test_missing_optional_s2b_is_skipped_not_pass(tmp_path):
    report = check_eval_manifests([
        ManifestSpec("v1", _write(tmp_path / "v1.jsonl",
                                  [_table("DOCA-P01-T01", SHA_A, 1)])),
        ManifestSpec("v2", _write(tmp_path / "v2.jsonl",
                                  [_table("DOCB-P01-T01", SHA_B, 1)])),
        ManifestSpec("s2b", tmp_path / "absent.jsonl", required=False),
    ])
    assert report["status"] == "partial"
    assert report["ok"] is False
    assert report["skipped"] == ["s2b"]
    assert report["sets"]["s2b"]["status"] == "skipped"
    assert report["findings"] == []


def test_missing_required_manifest_fails(tmp_path):
    report = check_eval_manifests([
        ManifestSpec("v1", tmp_path / "absent.jsonl"),
    ])
    assert report["status"] == "fail"
    assert report["sets"]["v1"]["status"] == "fail"
    assert _codes(report) == {"eval_manifest_missing"}


def test_conflict_marks_every_involved_set_failed(tmp_path):
    report = _check(tmp_path, {
        "v1": [_table("DOCA-P01-T01", SHA_A, 1)],
        "v2": [_table("DOCB-P01-T01", SHA_A, 1)],
    })
    assert report["status"] == "fail"
    assert report["sets"]["v1"]["status"] == "fail"
    assert report["sets"]["v2"]["status"] == "fail"


def test_missing_optional_s2b_remains_skipped_when_v1_v2_conflict(tmp_path):
    report = check_eval_manifests([
        ManifestSpec("v1", _write(tmp_path / "v1.jsonl",
                                  [_table("DOCA-P01-T01", SHA_A, 1)])),
        ManifestSpec("v2", _write(tmp_path / "v2.jsonl",
                                  [_table("DOCB-P01-T01", SHA_A, 1)])),
        ManifestSpec("s2b", tmp_path / "absent.jsonl", required=False),
    ])
    assert report["sets"]["v1"]["status"] == "fail"
    assert report["sets"]["v2"]["status"] == "fail"
    assert report["sets"]["s2b"]["status"] == "skipped"
    assert report["skipped"] == ["s2b"]
    assert report["status"] == "fail"


def test_cli_json_and_text_agree_on_skipped_s2b(tmp_path, capsys):
    from tools.validate_manifests import main

    v1 = _write(tmp_path / "v1.jsonl", [_table("DOCA-P01-T01", SHA_A, 1)])
    v2 = _write(tmp_path / "v2.jsonl", [_table("DOCB-P01-T01", SHA_B, 1)])
    args = ["--v1", str(v1), "--v2", str(v2)]

    assert main(args) == 3
    text = capsys.readouterr().out
    assert "v1: PASS" in text
    assert "v2: PASS" in text
    assert "s2b: SKIPPED" in text
    assert "overall: PARTIAL" in text

    assert main(args + ["--json"]) == 3
    payload = json.loads(capsys.readouterr().out)
    assert payload["sets"]["s2b"]["status"] == "skipped"
    assert payload["sets"]["v1"]["status"] == "pass"
    assert payload["status"] == "partial"


def test_cli_json_and_text_agree_on_failed_conflict_with_skipped_s2b(
        tmp_path, capsys):
    from tools.validate_manifests import main

    # Same physical table in v1 and v2 is a cross-set conflict, while the
    # default S2b path is optional and therefore absent.
    v1 = _write(tmp_path / "v1.jsonl", [_table("DOCA-P01-T01", SHA_A, 1)])
    v2 = _write(tmp_path / "v2.jsonl", [_table("DOCB-P01-T01", SHA_A, 1)])
    args = ["--v1", str(v1), "--v2", str(v2)]

    assert main(args) == 1
    text = capsys.readouterr().out
    assert "eval_manifest_cross_manifest_identity_collision" in text
    assert "v1: FAIL" in text
    assert "v2: FAIL" in text
    assert "s2b: SKIPPED" in text
    assert "overall: FAIL" in text

    assert main(args + ["--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "fail"
    assert payload["ok"] is False
    assert payload["skipped"] == ["s2b"]
    assert {name: entry["status"] for name, entry in payload["sets"].items()} == {
        "v1": "fail", "v2": "fail", "s2b": "skipped"}
