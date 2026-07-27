from datetime import UTC, datetime

from app.domain.access.integrity import AccessIntegritySignalStatus
from app.services.access.access_integrity import AccessIntegrityEngine
from app.domain.access.integrity import AccessIntegrityContext
from app.services.lnurl.integrity_signals import collect_lnurl_signals

NOW = datetime(2026, 7, 26, tzinfo=UTC)


def test_valid_replay_expiry_domain_and_signature_signals() -> None:
    valid = collect_lnurl_signals(
        {"lnurl_signature_valid": True, "lnurl_k1_consumed": True, "lnurl_action_matched": True},
        NOW,
    )[0]
    replay = collect_lnurl_signals({"lnurl_k1_reused": True}, NOW)[0]
    expired = collect_lnurl_signals({"lnurl_k1_expired": True}, NOW)[0]
    mismatch = collect_lnurl_signals({"lnurl_domain_mismatch": True}, NOW)[0]
    invalid = collect_lnurl_signals({"lnurl_signature_valid": False}, NOW)[0]
    assert valid.status is AccessIntegritySignalStatus.HEALTHY
    assert replay.hard_cap == mismatch.hard_cap == 20
    assert expired.score_delta > 0 and invalid.score_delta == 0
    assert "not treasury ownership" in valid.explanation


def test_personal_payerdata_comments_and_unsettled_invoice_add_no_assurance() -> None:
    base = {
        "lnurl_signature_valid": True,
        "lnurl_k1_consumed": True,
        "lnurl_action_matched": True,
        "payment_relevant": True,
        "entitlement_active": True,
        "entitlement_status": "unavailable",
    }
    one = AccessIntegrityEngine().calculate(
        AccessIntegrityContext("hmac:p", "lightning_wallet_principal", base, NOW)
    )
    two = AccessIntegrityEngine().calculate(
        AccessIntegrityContext(
            "hmac:p",
            "lightning_wallet_principal",
            base
            | {
                "payer_email": "redacted",
                "payer_name": "redacted",
                "comment_allowed": 100,
                "invoice_issued": True,
            },
            NOW,
        )
    )
    assert one.score == two.score
    settled = AccessIntegrityEngine().calculate(
        AccessIntegrityContext(
            "hmac:p", "lightning_wallet_principal", base | {"settlement_verified": True}, NOW
        )
    )
    assert settled.score > one.score
