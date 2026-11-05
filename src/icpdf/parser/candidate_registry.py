"""Candidate Registry: every cell becomes a table-bound, immutable candidate."""

from __future__ import annotations

import re

from icpdf.domain.candidate import (
    Candidate,
    CandidateSet,
    CandidateType,
    ColumnRole,
    SourceTextType,
)
from icpdf.domain.table import ExtractionMethod, Table
from icpdf.parser.header_semantics import role_for_header

_NUMERIC = re.compile(r"^[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)(?:e[+-]?\d+)?$", re.I)


def column_role(header: str | None) -> ColumnRole:
    """Backward-compatible alias for the Layer 4 role mapper."""
    return role_for_header(header)


def _candidate_type(role: ColumnRole, is_first: bool) -> CandidateType:
    if role is ColumnRole.SYMBOL:
        return CandidateType.SYMBOL
    if role is ColumnRole.UNIT:
        return CandidateType.UNIT
    if role is ColumnRole.CONDITION:
        return CandidateType.CONDITION
    if is_first and role is ColumnRole.UNKNOWN:
        return CandidateType.ROW_LABEL
    return CandidateType.VALUE


def _normalized(text: str) -> str | None:
    token = text.strip()
    return token if _NUMERIC.match(token) else None


def build_candidates(run_id: str, document_id: str,
                     tables: list[Table],
                     column_roles: dict[str, list[ColumnRole]] | None = None) -> CandidateSet:
    candidates: list[Candidate] = []
    for table in tables:
        roles = (column_roles or {}).get(table.table_id) \
            or [column_role(h) for h in table.headers]
        header_cell_ids: dict[int, str] = {}
        for header in table.header_cells:
            header_cell_ids[header.column_id] = header.header_cell_id
        unit_text: str | None = None
        for row_index, row in enumerate(table.rows, 1):
            for cell in row.cells:
                if roles and cell.column_id < len(roles) and roles[cell.column_id] is ColumnRole.UNIT:
                    if cell.text.strip():
                        unit_text = cell.text.strip(" []()")
        for row_index, row in enumerate(table.rows, 1):
            for cell in row.cells:
                role = roles[cell.column_id] if cell.column_id < len(roles) else ColumnRole.UNKNOWN
                header = (table.headers[cell.column_id]
                          if cell.column_id < len(table.headers) else "")
                base_role = role_for_header(header) if header else ColumnRole.UNKNOWN
                if header and role is base_role:
                    role_source = "header_text"
                elif role is ColumnRole.UNKNOWN:
                    role_source = "fail_closed"
                else:
                    role_source = "heuristic"
                candidates.append(Candidate(
                    candidate_id=f"{document_id}:{cell.cell_id}",
                    document_id=document_id,
                    table_id=table.table_id,
                    row_id=row.row_id,
                    cell_id=cell.cell_id,
                    page_number=cell.page_number,
                    bbox=cell.bbox,
                    raw_text=cell.text,
                    normalized_value=_normalized(cell.text),
                    unit=unit_text if role is not ColumnRole.UNIT else None,
                    column_role=role,
                    role_source=role_source,
                    role_header_cell_id=(header_cell_ids.get(cell.column_id)
                                         if header else None),
                    candidate_type=_candidate_type(role, cell.column_id == 0),
                    extraction_method=ExtractionMethod.TABLE_DETECTOR,
                    source_text_type=SourceTextType.NATIVE_PDF_TEXT,
                    reconstruction_status=table.reconstruction_status,
                ))
    return CandidateSet(run_id=run_id, document_id=document_id, candidates=candidates)
