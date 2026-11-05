"""Deterministic text extraction: blocks / lines / spans / words, all with bbox."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from icpdf.domain.common import BBox, NonEmptyStr
from icpdf.parser.coords import PageGeometry

import pymupdf as fitz


class TextWord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    word_id: NonEmptyStr
    text: str
    bbox: BBox


class TextLine(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    line_id: NonEmptyStr
    page_number: int = Field(ge=1)
    bbox: BBox
    text: str
    words: list[TextWord] = Field(default_factory=list)


class TextSpan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    span_id: NonEmptyStr
    bbox: BBox
    text: str
    font: str | None = None
    size: float | None = None


class TextBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    block_id: NonEmptyStr
    page_number: int = Field(ge=1)
    bbox: BBox
    lines: list[TextLine] = Field(default_factory=list)
    spans: list[TextSpan] = Field(default_factory=list)


def _line_bbox(words: list[tuple[float, float, float, float, str]]) -> BBox:
    return (min(w[0] for w in words), min(w[1] for w in words),
            max(w[2] for w in words), max(w[3] for w in words))


def extract_text_blocks(page, page_number: int, geometry: PageGeometry) -> list[TextBlock]:
    """Extract native PDF text. Never fabricates text on a page with no text layer."""
    raw = page.get_text("dict")
    blocks_out: list[TextBlock] = []
    for block_index, block in enumerate(raw.get("blocks", [])):
        if block.get("type") != 0:
            continue
        lines_out: list[TextLine] = []
        spans_out: list[TextSpan] = []
        for line_index, line in enumerate(block.get("lines", [])):
            line_words: list[tuple[float, float, float, float, str]] = []
            span_texts: list[str] = []
            for span_index, span in enumerate(line.get("spans", [])):
                text = str(span.get("text") or "")
                bbox = geometry.clamp_bbox(tuple(span.get("bbox") or (0, 0, 0, 0)))
                spans_out.append(TextSpan(
                    span_id=f"p{page_number}-b{block_index}-l{line_index}-s{span_index}",
                    bbox=bbox, text=text, font=span.get("font"),
                    size=float(span["size"]) if span.get("size") else None,
                ))
                span_texts.append(text)
                if text.strip():
                    line_words.append((bbox[0], bbox[1], bbox[2], bbox[3], text))
            if not line_words:
                continue
            line_bbox = geometry.clamp_bbox(_line_bbox(line_words))
            lines_out.append(TextLine(
                line_id=f"p{page_number}-b{block_index}-l{line_index}",
                page_number=page_number,
                bbox=line_bbox,
                text=" ".join(span_texts).strip(),
                words=[TextWord(word_id=f"p{page_number}-b{block_index}-l{line_index}-w{i}",
                                text=w[4], bbox=(w[0], w[1], w[2], w[3]))
                       for i, w in enumerate(line_words)],
            ))
        if lines_out:
            blocks_out.append(TextBlock(
                block_id=f"p{page_number}-b{block_index}",
                page_number=page_number,
                bbox=geometry.clamp_bbox(
                    (min(l.bbox[0] for l in lines_out), min(l.bbox[1] for l in lines_out),
                     max(l.bbox[2] for l in lines_out), max(l.bbox[3] for l in lines_out))),
                lines=lines_out, spans=spans_out,
            ))
    return blocks_out
