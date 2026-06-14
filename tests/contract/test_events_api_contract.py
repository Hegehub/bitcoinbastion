from app.services.events.outbox_service import MAX_EVENT_METADATA_BYTES, MAX_EVENT_PAYLOAD_BYTES


def test_event_outbox_contract_has_bounded_payloads() -> None:
    assert MAX_EVENT_PAYLOAD_BYTES == 65_536
    assert MAX_EVENT_METADATA_BYTES == 16_384
