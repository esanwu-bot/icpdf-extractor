# -*- coding: utf-8 -*-
"""Phase 0 contract tests: positive and negative, no PDF parsing required."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from icpdf.domain import (
    Candidate,
    CandidateSet,
    Cell,
    Document,
    Evidence,
    FormalParameterSet,
    Parameter,
    Product,
    Table,
    TableRow,
    TableType,
    ReconstructionStatus,
    IdentityEvidence,
)

NOW = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
SHA = "a" * 64


def _document(**kw) -> Document:
    base = dict(document_id="doc-1", filename="sample.pdf", sha256=SHA,
                page_count=2, document_type="datasheet",
                parser_version="0.1.0-phase0", created_at=NOW,
                page_sizes=[(595.0, 842.0)] * 2, page_rotations=[0, 0])
    base.update(kw)
    return Document(**base)


def _cell(cell_id="c1", row_id="r1", column_id=0, page=1, bbox=(10, 10, 50, 20)) -> Cell:
    return Cell(cell_id=cell_id, row_id=row_id, column_id=column_id,
                text="3.3", bbox=bbox, page_number=page)


def _candidate(cid="cand-1", table="t1", row="r1", cell="c1", **kw) -> Candidate:
    base = dict(candidate_id=cid, document_id="doc-1", table_id=table,
                row_id=row, cell_id=cell, page_number=1,
                bbox=(10, 10, 50, 20), raw_text="3.3",
                column_role="value", candidate_type="value")
    base.update(kw)
    return Candidate(**base)


# ---------------------------------------------------------------- Document

def test_document_accepts_valid_identity():
    doc = _document()
    assert doc.sha256 == SHA and doc.page_count == 2


def test_document_rejects_bad_sha():
    with pytest.raises(ValidationError):
        _document(sha256="zz")


def test_document_rejects_naive_datetime():
    with pytest.raises(ValidationError):
        _document(created_at=datetime(2026, 11, 5, 12, 0))


def test_document_rejects_partial_page_sizes():
    with pytest.raises(ValidationError):
        _document(page_sizes=[(595.0, 842.0)])


# ---------------------------------------------------------------- Product

def test_product_keeps_requested_and_normalized_mpn_separate():
    p = Product(product_id="p1", document_id="doc-1",
                requested_mpn="AFE7950EVM", normalized_mpn="AFE7950EVM")
    assert p.requested_mpn == "AFE7950EVM"


def test_product_requires_evidence_when_normalized_differs():
    with pytest.raises(ValidationError):
        Product(product_id="p1", document_id="doc-1",
                requested_mpn="FOO", normalized_mpn="BAR")


def test_product_accepts_evidence_for_normalization():
    p = Product(product_id="p1", document_id="doc-1",
                requested_mpn="FOO", normalized_mpn="BAR",
                identity_evidence=[IdentityEvidence(kind="title",
                                                    page_number=1, raw_text="BAR")])
    assert p.identity_evidence[0].raw_text == "BAR"


# ---------------------------------------------------------------- Table / Cell

def _table(**kw) -> Table:
    base = dict(table_id="t1", document_id="doc-1", page_number=1,
                bbox=(0, 0, 100, 100), table_type=TableType.ELECTRICAL_CHARACTERISTICS,
                headers=["Symbol", "Min", "Typ", "Max"],
                rows=[TableRow(row_id="r1", cells=[_cell()])],
                detection_method="vector_lines", confidence=0.9,
                reconstruction_status=ReconstructionStatus.RECONSTRUCTED)
    base.update(kw)
    return Table(**base)


def test_table_accepts_well_formed_rows():
    t = _table()
    assert t.rows[0].cells[0].cell_id == "c1"


def test_table_rejects_duplicate_cell_ids():
    with pytest.raises(ValidationError):
        _table(rows=[TableRow(row_id="r1", cells=[_cell()]),
                     TableRow(row_id="r2", cells=[_cell(row_id="r2")])])


def test_table_rejects_cell_outside_page_range():
    with pytest.raises(ValidationError):
        _table(rows=[TableRow(row_id="r1", cells=[_cell(page=3)])])


def test_table_unresolved_must_explain():
    with pytest.raises(ValidationError):
        _table(reconstruction_status=ReconstructionStatus.UNRESOLVED)


def test_row_rejects_mismatched_row_id():
    with pytest.raises(ValidationError):
        TableRow(row_id="r1", cells=[_cell(row_id="r2")])


def test_bbox_must_be_ordered():
    with pytest.raises(ValidationError):
        _cell(bbox=(50, 10, 10, 20))


# ---------------------------------------------------------------- Candidate

def test_candidate_keeps_table_binding():
    c = _candidate()
    assert c.table_id == "t1" and c.row_id == "r1" and c.cell_id == "c1"


def test_candidate_rejects_blank_raw_text():
    with pytest.raises(ValidationError):
        _candidate(raw_text="   ")


def test_candidate_set_rejects_duplicate_ids():
    with pytest.raises(ValidationError):
        CandidateSet(run_id="run-1", document_id="doc-1",
                     candidates=[_candidate(), _candidate()])


def test_candidate_set_rejects_cross_document_candidate():
    with pytest.raises(ValidationError):
        CandidateSet(run_id="run-1", document_id="doc-1",
                     candidates=[_candidate(document_id="doc-2")])


def test_same_number_in_two_tables_stays_two_candidates():
    a = _candidate(cid="cand-t1", table="t1", row="r1", cell="c1")
    b = _candidate(cid="cand-t2", table="t2", row="r1", cell="c1")
    s = CandidateSet(run_id="run-1", document_id="doc-1", candidates=[a, b])
    assert len(s.candidates) == 2
    assert {c.table_id for c in s.candidates} == {"t1", "t2"}


# ---------------------------------------------------------------- Evidence

def test_evidence_requires_valid_sha_and_nonblank_text():
    with pytest.raises(ValidationError):
        Evidence(evidence_id="e1", document_sha256="bad", page_number=1,
                 table_id="t1", row_id="r1", cell_id="c1",
                 bbox=(0, 0, 10, 10), raw_text="3.3")
    with pytest.raises(ValidationError):
        Evidence(evidence_id="e1", document_sha256=SHA, page_number=1,
                 table_id="t1", row_id="r1", cell_id="c1",
                 bbox=(0, 0, 10, 10), raw_text="  ")


def test_cell_evidence_requires_table_row_cell_ids():
    with pytest.raises(ValidationError):
        Evidence(evidence_id="e1", document_sha256=SHA, page_number=1,
                 bbox=(0, 0, 10, 10), raw_text="3.3")


def test_paragraph_evidence_may_omit_table_ids():
    ev = Evidence(evidence_id="e2", document_sha256=SHA, page_number=1,
                  bbox=(0, 0, 10, 10), raw_text="typical 3.3 V",
                  evidence_type="paragraph")
    assert ev.table_id is None and ev.evidence_type.value == "paragraph"


def test_candidate_records_source_text_type_and_method():
    c = _candidate(extraction_method="table_detector",
                   source_text_type="native_pdf_text",
                   reconstruction_status="reconstructed")
    assert c.source_text_type.value == "native_pdf_text"
    assert c.extraction_method.value == "table_detector"


# ---------------------------------------------------------------- Parameter

def _parameter(**kw) -> Parameter:
    base = dict(parameter_id="p1", name="VOH", category="electrical",
                value="3.3", unit="V", applicable_mpn="X1", table_id="t1",
                evidence_ids=["e1"], verification_status="verified")
    base.update(kw)
    return Parameter(**base)


def test_formal_parameter_requires_evidence():
    with pytest.raises(ValidationError):
        _parameter(evidence_ids=[])


def test_unresolved_parameter_requires_reason():
    with pytest.raises(ValidationError):
        _parameter(verification_status="unresolved", evidence_ids=[])


def test_parameter_requires_a_value_field():
    with pytest.raises(ValidationError):
        _parameter(value=None)


def test_formal_set_rejects_unresolved():
    with pytest.raises(ValidationError):
        FormalParameterSet(document_id="doc-1", product_id="p1",
                           parameters=[_parameter(verification_status="unresolved",
                                                  unresolved_reason="no row")])


def test_formal_set_accepts_verified_parameter():
    s = FormalParameterSet(document_id="doc-1", product_id="p1",
                           parameters=[_parameter()])
    assert s.parameters[0].evidence_ids == ["e1"]
