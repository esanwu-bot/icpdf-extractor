"""Byte-preserving JSON helpers for read-only artifact validation."""

from __future__ import annotations

import json
from pathlib import Path

_WHITESPACE = " \t\r\n"


class JsonMemberError(ValueError):
    """A top-level member cannot be extracted unambiguously."""


class JsonMemberMissing(JsonMemberError):
    """The requested top-level member occurs zero times."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"missing top-level member: {name}")


class JsonMemberDuplicate(JsonMemberError):
    """The requested top-level member occurs more than once."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"duplicate top-level member: {name}")


class JsonMemberParseError(JsonMemberError):
    """The bytes are not a well-formed UTF-8 JSON object."""


def _skip_space(text: str, index: int) -> int:
    while index < len(text) and text[index] in _WHITESPACE:
        index += 1
    return index


def _extract(text: str, name: str) -> tuple[int, int]:
    decoder = json.JSONDecoder()
    index = _skip_space(text, 0)
    if index >= len(text) or text[index] != "{":
        raise JsonMemberParseError("JSON root is not an object")
    index += 1
    span: tuple[int, int] | None = None
    while True:
        index = _skip_space(text, index)
        if index < len(text) and text[index] == "}":
            break
        if index >= len(text) or text[index] != '"':
            raise JsonMemberParseError("malformed JSON object")
        # scanstring decodes escapes, so "table\u005fparams" is the same key.
        key, index = json.decoder.scanstring(text, index + 1, True)
        index = _skip_space(text, index)
        if index >= len(text) or text[index] != ":":
            raise JsonMemberParseError("malformed JSON member")
        start = _skip_space(text, index + 1)
        _, end = decoder.raw_decode(text, start)
        if key == name:
            if span is not None:
                raise JsonMemberDuplicate(name)
            span = (start, end)
        index = _skip_space(text, end)
        if index < len(text) and text[index] == ",":
            index += 1
            continue
        if index < len(text) and text[index] == "}":
            break
        raise JsonMemberParseError("malformed JSON object")
    index = _skip_space(text, index + 1)
    if index != len(text):
        raise JsonMemberParseError("trailing data after the JSON object")
    if span is None:
        raise JsonMemberMissing(name)
    return span


def extract_json_member_bytes(raw: bytes, name: str) -> bytes:
    """Return the exact bytes of one top-level object member, unparsed.

    Exactly one occurrence is required. The parsed value is discarded; the
    original byte span is returned, so a validator re-parses the same bytes and
    a duplicate key inside the value is never collapsed first.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise JsonMemberParseError(f"invalid UTF-8: {exc}") from exc
    try:
        span = _extract(text, name)
    except JsonMemberError:
        raise
    except (json.JSONDecodeError, ValueError) as exc:
        raise JsonMemberParseError(f"malformed JSON: {exc}") from exc
    start = len(text[:span[0]].encode("utf-8"))
    end = len(text[:span[1]].encode("utf-8"))
    return raw[start:end]


def read_manifest_rows(path: str | Path) -> list[tuple[int, object]]:
    """Read a JSONL manifest, or a JSON document holding a list of items."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".jsonl":
        return [(number, json.loads(line))
                for number, line in enumerate(text.splitlines(), 1)
                if line.strip()]
    document = json.loads(text)
    items = document.get("items") if isinstance(document, dict) else document
    if not isinstance(items, list):
        raise ValueError(f"{path} does not contain a list of items")
    return list(enumerate(items, 1))
