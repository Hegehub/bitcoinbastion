from scripts.check_route_api_parity import has_reflex_route


def test_reflex_route_detection_supports_direct_and_registry_routes() -> None:
    app_source = 'app.add_page(trace_page, route="/trace")'
    registry_source = 'PublicRouteSpec("/platform", "Platform", platform_page)'

    assert has_reflex_route(app_source, registry_source, "/trace")
    assert has_reflex_route(app_source, registry_source, "/platform")
    assert not has_reflex_route(app_source, registry_source, "/missing")
