"""Raw-byte top-level JSON member extraction."""

from __future__ import annotations

import pytest

from icpdf.eval.jsonio import (
    JsonMemberDuplicate,
    JsonMemberMissing,
    JsonMemberParseError,
    extract_json_member_bytes,
)


def test_returns_the_exact_original_byte_span():
    raw = ('{"note":"中文","table_params":{"snapshot_version":"table-params/v1",'
           ' "params":{}},"tail":true}').encode("utf-8")
    assert extract_json_member_bytes(raw, "table_params") == (
        b'{"snapshot_version":"table-params/v1", "params":{}}')


def test_internal_whitespace_is_preserved_and_trailing_space_is_not():
    raw = b'{"table_params" :  {"x": 1} , "b": 2}'
    assert extract_json_member_bytes(raw, "table_params") == b'{"x": 1}'


def test_zero_occurrences_is_an_explicit_missing_error():
    with pytest.raises(JsonMemberMissing):
        extract_json_member_bytes(b'{"other":1}', "table_params")


def test_two_top_level_members_are_refused_without_choosing_one():
    raw = b'{"table_params":{"a":1},"table_params":{"a":2}}'
    with pytest.raises(JsonMemberDuplicate):
        extract_json_member_bytes(raw, "table_params")


def test_escaped_key_is_the_same_key():
    raw = br'{"table\u005fparams":{"a":1}}'
    assert extract_json_member_bytes(raw, "table_params") == b'{"a":1}'


def test_escaped_duplicate_is_still_a_duplicate():
    raw = br'{"table_params":1,"table\u005fparams":2}'
    with pytest.raises(JsonMemberDuplicate):
        extract_json_member_bytes(raw, "table_params")


def test_key_text_inside_a_value_is_not_a_member():
    raw = b'{"note":"table_params","table_params":{"a":1}}'
    assert extract_json_member_bytes(raw, "table_params") == b'{"a":1}'


def test_nested_same_name_key_is_not_the_top_level_member():
    raw = b'{"table_params":{"table_params":1,"x":2}}'
    assert extract_json_member_bytes(raw, "table_params") == (
        b'{"table_params":1,"x":2}')


def test_duplicate_key_inside_the_value_is_not_collapsed():
    raw = b'{"table_params":{"a":1,"a":2}}'
    assert extract_json_member_bytes(raw, "table_params") == b'{"a":1,"a":2}'


@pytest.mark.parametrize("raw", [
    b'{"table_params":',
    b'{"table_params":{"a":1}',
    b'{"table_params":"\\q"}',
    b'{"table_params":tru}',
    b'[]',
    b'{"table_params":{}} trailing',
    b'\xff{"table_params":{}}',
])
def test_malformed_input_is_a_parse_error(raw):
    with pytest.raises(JsonMemberParseError):
        extract_json_member_bytes(raw, "table_params")


def test_empty_object_reports_missing():
    with pytest.raises(JsonMemberMissing):
        extract_json_member_bytes(b'{}', "table_params")
