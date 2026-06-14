from collections.abc import Mapping, Sequence
from enum import StrEnum


class SafetyFlag(StrEnum):
    ADVISORY_ONLY = "advisory_only"
    NOT_FINANCIAL_ADVICE = "not_financial_advice"
    NOT_LEGAL_VERIFICATION = "not_legal_verification"
    NOT_BITCOIN_CONSENSUS_PROOF = "not_bitcoin_consensus_proof"
    NO_CUSTODY = "no_custody"
    PUBLIC_DATA_ONLY = "public_data_only"
    OPERATOR_REVIEW_REQUIRED = "operator_review_required"
    DEGRADED_DATA_VISIBLE = "degraded_data_visible"
    PROVIDER_DISAGREEMENT_VISIBLE = "provider_disagreement_visible"
    STALE_DATA_VISIBLE = "stale_data_visible"
    CORRELATION_NOT_CAUSATION = "correlation_not_causation"
    HISTORICAL_SIMILARITY_NOT_PREDICTION = "historical_similarity_not_prediction"
    NO_AUTO_EXECUTION = "no_auto_execution"


class EventPayloadSafetyError(ValueError):
    pass


_SENSITIVE_PHRASES = (
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "keystore",
    "12 words",
    "24 words",
    "signing material",
    "secret recovery phrase",
    "recovery phrase",
    "jwt secret",
    "api token",
    "database url",
    "provider credential",
)

_MISLEADING_PARTS = (
    ("clean", "address"),
    ("dirty", "address"),
    ("criminal", "address"),
    ("guaranteed", "safe"),
    ("approved", "payment"),
    ("verified", "illicit"),
)


def _iter_values(value: object) -> Sequence[object]:
    if isinstance(value, Mapping):
        return [item for pair in value.items() for item in pair]
    if isinstance(value, (list, tuple, set, frozenset)):
        return list(value)
    return []


def _assert_text_safe(value: str) -> None:
    lowered = value.casefold()
    for phrase in _SENSITIVE_PHRASES:
        if phrase in lowered:
            raise EventPayloadSafetyError("Event payload contains sensitive wallet material.")
    for first, second in _MISLEADING_PARTS:
        if first in lowered and second in lowered:
            raise EventPayloadSafetyError("Event payload contains misleading safety wording.")


def assert_event_payload_safe(payload: Mapping[str, object]) -> None:
    def visit(value: object) -> None:
        if isinstance(value, str):
            _assert_text_safe(value)
        for child in _iter_values(value):
            visit(child)

    visit(payload)
