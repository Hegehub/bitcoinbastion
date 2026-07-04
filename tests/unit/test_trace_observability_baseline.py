from app.services.bastion_trace.trace_metrics import TRACE_REQUESTS
from app.services.bastion_trace.trace_runtime_events import create_event, get_event


def test_metrics_labels_are_bounded() -> None:
    assert set(TRACE_REQUESTS._labelnames) <= {
        "tier",
        "band",
        "status",
        "event_type",
        "source_type",
        "severity",
        "operation",
    }


def test_runtime_event_create_and_get() -> None:
    event = create_event("TRACE_REPORT_CREATED", "INFO", "analyze", "success", "ok")
    loaded = get_event(int(event["id"]))
    assert loaded is not None
    assert loaded["event_type"] == "TRACE_REPORT_CREATED"
