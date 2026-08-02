from app.services.access.crypto.issuer_envelope import BastionIssuedObjectType


def test_wallet_and_lnurl_entitlements_share_object_envelope_family():
    assert BastionIssuedObjectType.WALLET_SUBSCRIPTION_ENTITLEMENT.value.endswith(
        "subscription_entitlement"
    )
    assert BastionIssuedObjectType.LIGHTNING_SUBSCRIPTION_ENTITLEMENT.value.endswith(
        "subscription_entitlement"
    )
