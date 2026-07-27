from pathlib import Path

from prometheus_client.metrics import MetricWrapperBase

import app.services.access.observability as access_metrics
import app.services.lnurl.metrics as lnurl_metrics
import app.services.wallet_auth.metrics as wallet_metrics


FORBIDDEN_LABELS = {
    "principal_hash",
    "actor_hash",
    "wallet_address",
    "linking_key",
    "k1",
    "session_id",
    "device_fingerprint",
    "invoice_hash",
    "payment_hash",
    "preimage",
    "merchant_id",
}


def test_metric_definitions_have_no_identifier_labels() -> None:
    metrics = [
        value
        for module in (access_metrics, lnurl_metrics, wallet_metrics)
        for value in vars(module).values()
        if isinstance(value, MetricWrapperBase)
    ]
    assert metrics
    for metric in metrics:
        assert FORBIDDEN_LABELS.isdisjoint(metric._labelnames)  # noqa: SLF001


def test_dashboard_has_no_user_level_queries() -> None:
    text = Path("deploy/kubernetes/observability/grafana-dashboard-wallet-lnurl.json").read_text()
    for forbidden in FORBIDDEN_LABELS | {"lightning_address", "wallet_identifier"}:
        assert f"by ({forbidden})" not in text
