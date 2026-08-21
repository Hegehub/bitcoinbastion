from datetime import UTC, datetime

from bastion_ui.domain.access.adapters import (
    adapt_access_challenge,
    adapt_access_checkout,
    adapt_access_offer,
    adapt_issued_access,
)
from bastion_ui.security.device_provider import UnavailableDeviceProvider
from bastion_ui.transport.generated_schemas import (
    AccessOfferOut,
    CheckoutOut,
    IssuanceChallengeOut,
    IssuedAccessOut,
)


def test_challenge_and_grant_adapters_are_typed_and_non_secret():
    now = datetime.now(UTC)
    challenge = adapt_access_challenge(IssuanceChallengeOut(
        challenge_id="challenge:a", checkout_id="checkout:a", canonical_payload="{}",
        protocol_version="bastion-access-issuance-v1", algorithm="Ed25519", expires_at=now,
    ))
    grant = adapt_issued_access(IssuedAccessOut(
        grant_id="grant:a", checkout_id="checkout:a", offer_revision_id="offer:v1",
        certificate_fingerprint="sha256:cert", device_key_fingerprint="sha256:device",
        capability="plus_pass", scopes=["signals:basic:read"], terms_version="terms-v1",
        status="active", issued_at=now, expires_at=now,
    ))
    assert challenge.protocol_version == "bastion-access-issuance-v1"
    assert grant.scopes == ("signals:basic:read",)
    assert "private" not in " ".join(type(grant).model_fields)


def test_device_provider_has_signing_but_no_private_key_extraction_api():
    provider = UnavailableDeviceProvider()
    assert hasattr(provider, "sign_access_challenge")
    assert not hasattr(provider, "private_key")
    assert not hasattr(provider, "get_private_key")


def test_offer_and_checkout_adapters_preserve_backend_frozen_terms():
    now = datetime.now(UTC)
    offer = adapt_access_offer(AccessOfferOut(
        offer_id="offer:a", revision_id="offer:a:v2", plan_code="plus_pass",
        capability="plus_pass", scopes=["signals:basic:read"], amount_sats=50_000,
        price_unit="sats", duration_days=30, terms_version="terms-v2",
        availability="active", limitations=["Backend-owned."],
    ))
    checkout = adapt_access_checkout(CheckoutOut(
        checkout_id="checkout:a", offer_id="offer:a", offer_revision_id="offer:a:v1",
        plan_code="plus_pass", capability="plus_pass", scopes=["signals:basic:read"],
        amount_sats=40_000, price_unit="sats", duration_days=20, terms_version="terms-v1",
        status="eligible", issuance_eligible=True, eligibility_reason="payment_settled",
        payment_intent_id=7, created_at=now, expires_at=now,
    ))
    assert offer.revision_id == "offer:a:v2"
    assert checkout.offer_revision_id == "offer:a:v1"
    assert checkout.amount_sats == 40_000 and checkout.duration_days == 20


def test_access_state_uses_generated_clients_and_has_no_browser_authority_fields():
    from pathlib import Path

    source = Path("bastion_ui/state/access_acquisition_state.py").read_text()
    for operation in (
        "get_access_offers_api_v1_access_offers_get",
        "create_access_checkout_api_v1_access_checkouts_post",
        "create_issuance_challenge_api_v1_access_issuance_challenges_post",
        "issue_access_api_v1_access_issuance_post",
        "get_issued_access_api_v1_access_issued__grant_id__get",
    ):
        assert operation in source
    assert "private_key" not in source
    assert "pop_verified" not in source
    assert "amount_sats=" not in source
    assert "duration_days=" not in source
    assert "capability=" not in source
