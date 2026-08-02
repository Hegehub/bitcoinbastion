import importlib

import app.services.lnurl.metrics as lnurl_metrics
import app.services.wallet_auth.metrics as wallet_metrics

from app.services.access.observability import endpoint_group, safe_inc
from app.services.access.observability_labels import (
    ActorTypeLabel,
    ReasonCodeLabel,
    normalize_label,
)


class BrokenCounter:
    def labels(self, **_: str) -> object:
        raise RuntimeError("metrics backend unavailable")


def test_metrics_failure_is_non_blocking() -> None:
    safe_inc(BrokenCounter(), {"result": "success"})  # type: ignore[arg-type]


def test_controlled_label_fallbacks_and_endpoint_normalization() -> None:
    assert normalize_label("bitcoin_wallet_principal", ActorTypeLabel) == "bitcoin_wallet_principal"
    assert normalize_label("principal-hash-here", ActorTypeLabel) == "unknown"
    assert normalize_label("raw internal failure", ReasonCodeLabel) == "unknown"
    assert endpoint_group("/v1/lnurl/pay/merchant/123") == "lnurl_pay"
    assert endpoint_group("/v1/unknown/object/123") == "unknown"


def test_metric_registration_is_idempotent_on_module_reload() -> None:
    importlib.reload(wallet_metrics)
    importlib.reload(lnurl_metrics)
