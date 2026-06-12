import pytest
from pydantic import ValidationError

from app.events.payloads import BastionEventEnvelope
from app.events.safety import EventPayloadSafetyError, SafetyFlag, assert_event_payload_safe
from app.events.types import BastionEventType, EventDomain


def test_safe_payload_passes() -> None:
    assert_event_payload_safe({"report_id": 42, "summary": "advisory review completed"})


@pytest.mark.parametrize(
    "material",
    [
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
        "jwt secret",
        "api token",
        "database url",
        "provider credential",
    ],
)
def test_forbidden_wallet_material_is_rejected(material: str) -> None:
    with pytest.raises(EventPayloadSafetyError):
        assert_event_payload_safe({"operator_note": f"do not include {material}"})


def test_nested_forbidden_material_is_rejected() -> None:
    with pytest.raises(EventPayloadSafetyError):
        assert_event_payload_safe({"nested": [{"operator_note": "contains private key"}]})


@pytest.mark.parametrize(
    "misleading_wording",
    [
        "clean address",
        "dirty address",
        "criminal address",
        "guaranteed safe",
        "approved payment",
        "verified illicit",
    ],
)
def test_misleading_trace_wording_is_rejected(misleading_wording: str) -> None:
    with pytest.raises(EventPayloadSafetyError):
        assert_event_payload_safe({"trace_summary": misleading_wording})


def test_event_envelope_validates_payload_safety() -> None:
    with pytest.raises(ValidationError):
        BastionEventEnvelope(
            event_type=BastionEventType.TRACE_REPORT_CREATED,
            domain=EventDomain.TRACE,
            source_module="test",
            payload={"note": "contains xprv"},
            limitations=["Trace reports are advisory-only."],
            safety_flags=[SafetyFlag.ADVISORY_ONLY],
        )


def test_event_envelope_requires_matching_domain() -> None:
    with pytest.raises(ValidationError):
        BastionEventEnvelope(
            event_type=BastionEventType.SIGNAL_CREATED,
            domain=EventDomain.TRACE,
            source_module="test",
            payload={"signal_id": 1},
        )


def test_event_envelope_serializes_public_dict() -> None:
    envelope = BastionEventEnvelope(
        event_type=BastionEventType.TRACE_REPORT_CREATED,
        domain=EventDomain.TRACE,
        source_module="test",
        aggregate_type="trace_report",
        aggregate_id="42",
        payload={"report_id": 42},
        limitations=["Trace reports are advisory-only."],
        safety_flags=[SafetyFlag.ADVISORY_ONLY, SafetyFlag.NO_CUSTODY],
    )

    serialized = envelope.public_dict()
    assert serialized["event_type"] == "trace.report.created"
    assert serialized["domain"] == "trace"
    assert serialized["safety_flags"] == ["advisory_only", "no_custody"]
