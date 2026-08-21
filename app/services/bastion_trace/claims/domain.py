from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib

from app.schemas.bastion_trace import TraceBand

CLAIM_SCHEMA_VERSION = "trace-claim-v1"


class TraceClaimSubjectKind(str, Enum):
    BITCOIN_ADDRESS = "bitcoin_address"


class TraceClaimPredicate(str, Enum):
    RISK_BAND = "risk_band"
    BITCOIN_NETWORK = "bitcoin_network"


class TraceClaimValueKind(str, Enum):
    RISK_BAND = "risk_band"
    BITCOIN_NETWORK = "bitcoin_network"


class TraceClaimProducerStatus(str, Enum):
    SUCCESS_WITH_CLAIM = "success_with_claim"
    NO_APPLICABLE_CLAIM = "no_applicable_claim"
    INSUFFICIENT_DATA = "insufficient_data"
    SOURCE_UNAVAILABLE = "source_unavailable"
    PRODUCER_FAILURE = "producer_failure"


@dataclass(frozen=True, slots=True)
class TraceClaimSubject:
    kind: TraceClaimSubjectKind
    object_id: str
    public_value: str


@dataclass(frozen=True, slots=True)
class RiskBandClaimValue:
    kind: TraceClaimValueKind
    band: TraceBand


@dataclass(frozen=True, slots=True)
class BitcoinNetworkClaimValue:
    kind: TraceClaimValueKind
    network: str


TraceClaimValue = RiskBandClaimValue | BitcoinNetworkClaimValue


@dataclass(frozen=True, slots=True)
class TraceClaimProvenance:
    input_references: tuple[str, ...]
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TraceClaim:
    id: str
    claim_schema_version: str
    capture_id: str
    subject: TraceClaimSubject
    predicate: TraceClaimPredicate
    value: TraceClaimValue
    producer_id: str
    producer_version: str
    source_id: str
    evaluated_at: datetime
    provenance: TraceClaimProvenance
    confidence: float | None = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        expected = {
            TraceClaimPredicate.RISK_BAND: TraceClaimValueKind.RISK_BAND,
            TraceClaimPredicate.BITCOIN_NETWORK: TraceClaimValueKind.BITCOIN_NETWORK,
        }[self.predicate]
        if self.value.kind is not expected:
            raise ValueError("claim predicate and value kind are incompatible")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("claim confidence must be between zero and one")


@dataclass(frozen=True, slots=True)
class TraceClaimProducerResult:
    producer_id: str
    status: TraceClaimProducerStatus
    claims: tuple[TraceClaim, ...] = ()
    limitation: str | None = None


def stable_claim_subject_id(kind: TraceClaimSubjectKind, value: str) -> str:
    return _stable_id("trace_claim_subject", kind.value, value)


def stable_claim_id(
    *,
    capture_id: str,
    subject_id: str,
    predicate: TraceClaimPredicate,
    producer_id: str,
    producer_version: str,
    source_id: str,
    value: TraceClaimValue,
    input_references: tuple[str, ...],
) -> str:
    value_part = value.band.value if isinstance(value, RiskBandClaimValue) else value.network
    return _stable_id(
        "trace_claim",
        CLAIM_SCHEMA_VERSION,
        capture_id,
        subject_id,
        predicate.value,
        producer_id,
        producer_version,
        source_id,
        value.kind.value,
        value_part,
        *sorted(input_references),
    )


def _stable_id(namespace: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join((namespace, *parts)).encode()).hexdigest()[:24]
    return f"{namespace}:{digest}"
