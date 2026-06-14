from app.core import telemetry
from app.services.events.webhook_dispatcher import _event_domain_label, _event_type_family, _webhook_metric_status


def test_webhook_metric_labels_are_bounded() -> None:
    assert _event_domain_label("trace") == "trace"
    assert _event_domain_label("user-controlled-domain") == "unknown"
    assert _event_type_family("trace.report.created") == "trace"
    assert _event_type_family("attacker.event.type") == "unknown"
    assert _webhook_metric_status("delivered") == "delivered"
    assert _webhook_metric_status("delivery_id_whd_123") == "unknown"


def test_core_bounded_label_helper_drops_unapproved_values() -> None:
    assert telemetry.bounded_label("endpoint", "/api/v1/webhooks/123") == "unknown"
    assert telemetry.bounded_label("provider", "https://example.com/webhook") == "unknown"
    assert telemetry.bounded_label("status", "success") == "success"
