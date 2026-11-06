"""Formal parameter model: no unsupported value may enter the formal container."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .common import NonEmptyStr


class ParameterCategory(str, Enum):
    ELECTRICAL = "electrical"
    ABSOLUTE_MAXIMUM = "absolute_maximum"
    RECOMMENDED_OPERATING = "recommended_operating"
    THERMAL = "thermal"
    MECHANICAL = "mechanical"
    TIMING = "timing"
    OTHER = "other"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    AUDITED = "audited"
    UNVERIFIED = "unverified"
    UNRESOLVED = "unresolved"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


#: Statuses allowed in the formal parameter container.
FORMAL_STATUSES = frozenset({VerificationStatus.VERIFIED, VerificationStatus.AUDITED})
#: Statuses that must explain why they are not formal.
EXPLAINED_STATUSES = frozenset({
    VerificationStatus.UNRESOLVED,
    VerificationStatus.QUARANTINED,
    VerificationStatus.REJECTED,
})


class Parameter(BaseModel):
    """A parameter claim plus the evidence that supports it.

    Invariants:
    * `evidence_ids` is mandatory for formal statuses (verified / audited);
    * unresolved/quarantined/rejected rows must carry `unresolved_reason`;
    * at least one of value / min / typ / max must be present;
    * `applicable_mpn` and `table_id` are mandatory: a parameter is never global.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    parameter_id: NonEmptyStr
    name: NonEmptyStr
    category: ParameterCategory
    value: str | None = None
    unit: str | None = None
    min: str | None = None
    typ: str | None = None
    max: str | None = None
    conditions: str | None = None
    applicable_mpn: NonEmptyStr
    package: str | None = None
    table_id: NonEmptyStr
    evidence_ids: list[str] = Field(default_factory=list)
    verification_status: VerificationStatus
    unresolved_reason: str | None = None

    @model_validator(mode="after")
    def _check_parameter(self) -> "Parameter":
        if not any(str(x or "").strip() for x in (self.value, self.min, self.typ, self.max)):
            raise ValueError("parameter needs at least one of value/min/typ/max")
        if self.verification_status in FORMAL_STATUSES and not self.evidence_ids:
            raise ValueError("formal parameter must reference at least one evidence_id")
        if self.verification_status in EXPLAINED_STATUSES and not self.unresolved_reason:
            raise ValueError(
                f"{self.verification_status.value} parameter must carry unresolved_reason"
            )
        if any(not str(eid).strip() for eid in self.evidence_ids):
            raise ValueError("evidence_ids must not contain blank ids")
        return self


class FormalParameterSet(BaseModel):
    """The formal container. Any non-formal status is rejected at construction."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    document_id: NonEmptyStr
    product_id: NonEmptyStr
    parameters: list[Parameter] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_formal(self) -> "FormalParameterSet":
        ids: set[str] = set()
        for parameter in self.parameters:
            if parameter.verification_status not in FORMAL_STATUSES:
                raise ValueError(
                    "non-formal parameter in formal container: "
                    f"{parameter.parameter_id} ({parameter.verification_status.value})"
                )
            if parameter.parameter_id in ids:
                raise ValueError(f"duplicate parameter_id: {parameter.parameter_id}")
            ids.add(parameter.parameter_id)
        return self
