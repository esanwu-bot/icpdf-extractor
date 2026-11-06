"""S2b-Schema: version-dispatched snapshot serialization and validation."""

from __future__ import annotations

import json

import pytest

from icpdf.parser.config import (
    LOGICAL_FIELDS,
    TABLE_PARAMS_SNAPSHOT_VERSION,
    V1_FIELDS,
    V2_FIELDS,
    TableParams,
    UnsupportedTableParamsSnapshotVersion,
    load_table_params_snapshot,
    snapshot_sha256,
    table_params_sha256,
    table_params_snapshot,
    validate_table_params_snapshot,
)

V1 = "table-params/v1"
V2 = "table-params/v2"
FROZEN_V1_SHA = "82d4df4d1cb3cac9741831b0db36e19fa80c1829abc18b3f8b1ab4ee1c6b9f0a"


def _raw(document) -> bytes:
    return json.dumps(document, ensure_ascii=False).encode("utf-8")


def _validate(document, *, version: str, sha: str | None = None) -> list[str]:
    return validate_table_params_snapshot(
        _raw(document), expected_version=version,
        expected_sha256=sha if sha is not None else snapshot_sha256(document))


def test_declared_field_lists_match_the_model():
    declared = tuple(TableParams.model_fields)
    assert V1_FIELDS == declared[:20]
    assert LOGICAL_FIELDS == declared[20:]
    assert V2_FIELDS == declared
    assert len(V1_FIELDS) == 20 and len(LOGICAL_FIELDS) == 7


def test_v1_replay_reproduces_frozen_sha_and_has_no_logical_key():
    params = TableParams()
    snapshot = table_params_snapshot(params, version=V1)
    assert snapshot["snapshot_version"] == V1
    assert set(snapshot["params"]) == set(V1_FIELDS)
    assert not any(name.startswith("logical_") for name in snapshot["params"])
    assert table_params_sha256(params, version=V1) == FROZEN_V1_SHA
    assert _validate(snapshot, version=V1) == []


def test_v2_snapshot_contains_the_seven_logical_keys():
    snapshot = table_params_snapshot(TableParams())
    assert TABLE_PARAMS_SNAPSHOT_VERSION == V2
    assert snapshot["snapshot_version"] == V2
    assert set(snapshot["params"]) == set(V2_FIELDS)
    assert set(LOGICAL_FIELDS) <= set(snapshot["params"])
    assert snapshot["params"]["logical_label_min_band_ratio"] == 0.6
    assert snapshot["params"]["logical_short_label_max_chars"] == 12
    assert _validate(snapshot, version=V2) == []


def test_missing_and_unknown_keys_are_refused():
    snapshot = table_params_snapshot(TableParams())
    missing = json.loads(json.dumps(snapshot))
    del missing["params"]["logical_label_min_bands"]
    assert _validate(missing, version=V2) == [
        "table_params_snapshot_schema_invalid"]

    unknown = json.loads(json.dumps(snapshot))
    unknown["params"]["logical_not_a_field"] = 1
    assert _validate(unknown, version=V2) == [
        "table_params_snapshot_schema_invalid"]


def test_duplicate_key_is_distinct_from_parse_and_schema_errors():
    raw = (b'{"snapshot_version":"table-params/v1","params":'
           b'{"cell_gap_pt":8.0,"cell_gap_pt":9.0}}')
    assert validate_table_params_snapshot(
        raw, expected_version=V1, expected_sha256="0" * 64) == [
            "table_params_snapshot_duplicate_key"]

    nested = (b'{"snapshot_version":"table-params/v1","params":'
              b'{"cell_gap_pt":8.0},"extra":{"a":1,"a":2}}')
    assert validate_table_params_snapshot(
        nested, expected_version=V1, expected_sha256="0" * 64) == [
            "table_params_snapshot_duplicate_key"]


def test_invalid_utf8_and_truncated_json_are_parse_errors():
    for raw in (b"\xff\xfe", b"", b'{"snapshot_version":'):
        assert validate_table_params_snapshot(
            raw, expected_version=V1, expected_sha256="0" * 64) == [
                "table_params_snapshot_parse_error"]


def test_non_object_root_and_params_are_schema_errors_not_parse_errors():
    for document in ([], "text", 3, None):
        assert validate_table_params_snapshot(
            _raw(document), expected_version=V1,
            expected_sha256="0" * 64) == [
                "table_params_snapshot_schema_invalid"]

    params_string = {"snapshot_version": V1, "params": "text"}
    params_array = {"snapshot_version": V1, "params": []}
    for document in (params_string, params_array):
        assert validate_table_params_snapshot(
            _raw(document), expected_version=V1,
            expected_sha256="0" * 64) == [
                "table_params_snapshot_schema_invalid"]


def test_unknown_version_is_refused_by_serializer_and_validator():
    for function in (table_params_snapshot, table_params_sha256):
        with pytest.raises(UnsupportedTableParamsSnapshotVersion):
            function(TableParams(), version="table-params/v3")

    assert _validate({"snapshot_version": "table-params/v3",
                      "params": {}}, version="table-params/v3") == [
        "unsupported_table_params_snapshot_version"]

    assert _validate({"snapshot_version": V1, "params": {}},
                     version="table-params/v3") == [
        "unsupported_table_params_snapshot_version"]


def test_bool_is_refused_even_though_bool_is_an_int_subclass():
    for name in ("column_tolerance", "merge_shared_ratio"):
        document = json.loads(json.dumps(table_params_snapshot(TableParams())))
        document["params"][name] = True
        assert _validate(document, version=V2) == [
            "table_params_snapshot_schema_invalid"]


def test_int_field_refuses_a_float_value():
    document = json.loads(json.dumps(table_params_snapshot(TableParams())))
    document["params"]["column_tolerance"] = 2.0
    assert _validate(document, version=V2) == [
        "table_params_snapshot_schema_invalid"]


def test_integer_for_float_field_stays_an_integer_in_the_canonical_hash():
    document = json.loads(json.dumps(table_params_snapshot(TableParams())))
    document["params"]["merge_shared_ratio"] = 1
    loaded = load_table_params_snapshot(_raw(document))
    assert type(loaded.document["params"]["merge_shared_ratio"]) is int
    assert _validate(document, version=V2) == []
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"))
    assert '"merge_shared_ratio":1' in payload
    assert '"merge_shared_ratio":1.0' not in payload


def test_version_mismatch_and_sha_mismatch_are_refused():
    snapshot = table_params_snapshot(TableParams(), version=V1)
    assert _validate(snapshot, version=V2) == [
        "table_params_snapshot_version_mismatch"]
    assert _validate(snapshot, version=V1, sha="0" * 64) == [
        "table_params_snapshot_sha_mismatch"]


def test_bound_violation_is_a_schema_error():
    document = json.loads(json.dumps(table_params_snapshot(TableParams())))
    document["params"]["visual_full_height_coverage"] = 1.5
    assert _validate(document, version=V2) == [
        "table_params_snapshot_schema_invalid"]


def test_writer_refuses_a_non_finite_float():
    params = TableParams(cell_gap_pt=float("inf"))
    with pytest.raises(ValueError, match="non-finite"):
        table_params_snapshot(params)
