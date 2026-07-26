from prometheus_client import generate_latest

from app.services.lnurl.metrics import LNURLMetrics


def test_lnurl_metrics_never_expose_k1_invoice_or_address() -> None:
    metrics = LNURLMetrics()
    raw_k1 = "ab" * 32
    metrics.k1_event(flow=raw_k1, event=raw_k1, result="rejected", reason_code=raw_k1)
    metrics.address_resolution(
        address_class="alice@example.invalid",
        domain_class="example.invalid",
        result="success",
        reason_code="verified",
    )
    output = generate_latest().decode()
    relevant = "\n".join(
        line
        for line in output.splitlines()
        if line.startswith(("lnurl_auth_k1_events_total{", "lightning_address_resolutions_total{"))
    )
    assert raw_k1 not in relevant and "alice" not in relevant and "example.invalid" not in relevant
    assert 'reason_code="unknown"' in relevant


def test_payment_transition_has_only_controlled_states() -> None:
    LNURLMetrics().payment_transition(
        payment_method="lnurl_pay",
        from_state="invoice_issued",
        to_state="settled",
        result="settled",
        reason_code="unknown",
    )
    output = generate_latest().decode()
    assert 'payment_method="lnurl_pay"' in output and 'to_state="settled"' in output
