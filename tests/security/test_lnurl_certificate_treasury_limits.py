from app.services.access.principal_certificate_bridge import TREASURY_SCOPES


def test_lnurl_treasury_denylist_covers_ownership_and_policy():
    assert {"onchain:ownership", "treasury:policy:manage", "descriptor:manage"} <= TREASURY_SCOPES
