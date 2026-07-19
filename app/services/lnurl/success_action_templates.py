"""Server-controlled successAction message templates."""

from __future__ import annotations

import html
from typing import Mapping

from app.domain.lnurl.success_actions import LNURL_SUCCESS_DESCRIPTION_MAX_LENGTH, contains_forbidden_success_action_secret

_TEMPLATES: dict[str, str] = {
    "subscription_payment_received": "Payment complete. Bastion will verify your subscription activation.",
    "subscription_activation_ready": "Open Bastion to view activation status.",
    "subscription_upgrade_ready": "Open Bastion to finish your plan upgrade.",
    "receipt_available": "Receipt is available in Bastion.",
    "payregister_receipt_available": "Open your PayRegister receipt.",
    "vault_setup_available": "Open Bastion to continue vault setup.",
    "business_onboarding_available": "Open Bastion to continue business onboarding.",
}

_ALLOWED_FIELDS = {"product_display_name", "plan_display_name", "merchant_display_label", "receipt_display_reference"}


def render_success_action_template(code: str, fields: Mapping[str, str] | None = None) -> str:
    if code not in _TEMPLATES:
        raise ValueError("unknown_success_action_template")
    rendered = _TEMPLATES[code]
    for key, value in (fields or {}).items():
        if key not in _ALLOWED_FIELDS:
            raise ValueError("unsupported_success_action_template_field")
        safe_value = html.escape(str(value), quote=False)
        if contains_forbidden_success_action_secret(safe_value):
            raise ValueError("success_action_template_secret_rejected")
        rendered = rendered.replace("{" + key + "}", safe_value)
    if len(rendered) > LNURL_SUCCESS_DESCRIPTION_MAX_LENGTH or contains_forbidden_success_action_secret(rendered):
        raise ValueError("success_action_template_invalid")
    return rendered
