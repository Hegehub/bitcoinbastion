from bastion_ui.routes import PUBLIC_ROUTE_SPECS


def test_wallet_lnurl_and_payment_routes_exist() -> None:
    routes = {spec.route for spec in PUBLIC_ROUTE_SPECS}
    assert {
        "/wallet-auth",
        "/wallet-auth/devices",
        "/wallet-auth/recovery",
        "/wallet-auth/step-up",
        "/wallet-auth/subscription",
        "/wallet-auth/lightning/withdraw",
        "/access/checkout",
        "/lnurl/auth",
    } <= routes


def test_routes_render_without_backend_success_stubs() -> None:
    for spec in PUBLIC_ROUTE_SPECS:
        if spec.route.startswith(("/wallet-auth", "/lnurl", "/access")):
            assert spec.page() is not None
