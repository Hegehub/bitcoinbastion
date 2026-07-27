from prometheus_client import generate_latest

import app.services.access.observability  # noqa: F401
import app.services.lnurl.metrics  # noqa: F401
import app.services.wallet_auth.metrics  # noqa: F401


def test_required_metric_names_are_registered() -> None:
    output = generate_latest().decode()
    required = {
        "wallet_auth_challenges_total",
        "wallet_auth_proofs_total",
        "wallet_device_bindings_total",
        "wallet_pop_sessions_total",
        "wallet_step_up_requests_total",
        "lnurl_auth_challenges_total",
        "lnurl_auth_callbacks_total",
        "lnurl_auth_k1_events_total",
        "lnurl_pay_requests_total",
        "lnurl_verify_total",
        "lightning_address_resolutions_total",
        "lnurl_withdraw_requests_total",
        "lnurl_payment_entitlements_total",
        "bastion_access_policy_decisions_total",
        "bastion_access_revocation_checks_total",
        "bastion_access_security_alerts_total",
    }
    assert all(f"# HELP {name} " in output for name in required)
