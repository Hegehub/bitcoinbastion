"""Payment providers for Bastion Proof-of-Access Auth with lazy exports."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "BTCPayAccessPaymentProvider",
    "BTCPayConfigError",
    "BTCPayInvoiceCreateError",
    "BTCPayProviderUnavailable",
    "BTCPayUnsupportedEvent",
    "BTCPayWebhookParseError",
    "BTCPayWebhookVerificationError",
    "PaymentProviderHealth",
    "ManualGrantProvider",
    "PaymentProvider",
    "PaymentProviderInvoice",
    "PaymentProviderInvoiceStatus",
    "PaymentProviderWebhookEvent",
]

_EXPORT_MODULES = {
    "BTCPayAccessPaymentProvider": "app.services.access.payments.btcpay",
    "BTCPayConfigError": "app.services.access.payments.btcpay",
    "BTCPayInvoiceCreateError": "app.services.access.payments.btcpay",
    "BTCPayProviderUnavailable": "app.services.access.payments.btcpay",
    "BTCPayUnsupportedEvent": "app.services.access.payments.btcpay",
    "BTCPayWebhookParseError": "app.services.access.payments.btcpay",
    "BTCPayWebhookVerificationError": "app.services.access.payments.btcpay",
    "PaymentProviderHealth": "app.services.access.payments.btcpay",
    "ManualGrantProvider": "app.services.access.payments.manual",
    "PaymentProvider": "app.services.access.payments.base",
    "PaymentProviderInvoice": "app.services.access.payments.base",
    "PaymentProviderInvoiceStatus": "app.services.access.payments.base",
    "PaymentProviderWebhookEvent": "app.services.access.payments.base",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORT_MODULES:
        raise AttributeError(name)
    module = import_module(_EXPORT_MODULES[name])
    value = getattr(module, name)
    globals()[name] = value
    return value
