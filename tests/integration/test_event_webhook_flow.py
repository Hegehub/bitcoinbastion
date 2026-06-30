from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_event_outbox_and_webhook_dispatch_flow_files_exist() -> None:
    for path in [
        "app/events/registry.py",
        "app/services/events/event_bus_service.py",
        "app/services/events/outbox_service.py",
        "app/services/events/webhook_dispatcher.py",
        "app/services/events/webhook_signature.py",
        "app/services/events/webhook_delivery_log_service.py",
        "app/db/models/event_outbox.py",
    ]:
        assert (ROOT / path).exists(), path


def test_webhook_api_and_signature_headers() -> None:
    api = read("app/api/v1/webhooks.py")
    signature = read("app/services/events/webhook_signature.py")
    for route in [
        '@router.post(""',
        '@router.get(""',
        '@router.get("/{webhook_id}"',
        '@router.patch("/{webhook_id}"',
        '@router.delete("/{webhook_id}"',
        '@router.post("/{webhook_id}/test"',
        '@router.get("/{webhook_id}/deliveries"',
    ]:
        assert route in api
    for header in [
        "X-Bastion-Event",
        "X-Bastion-Timestamp",
        "X-Bastion-Signature",
        "X-Bastion-Delivery-ID",
    ]:
        assert header in signature
    assert "hmac" in signature
    assert "sha256" in signature
