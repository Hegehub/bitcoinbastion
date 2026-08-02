from __future__ import annotations

from starlette.requests import Request

from app.api.access_dependencies import _canonical_request_target, _extract_session_token


def request(path: str, headers: list[tuple[bytes, bytes]] | None = None) -> Request:
    return Request({"type": "http", "method": "GET", "path": path.split("?", 1)[0], "query_string": path.partition("?")[2].encode(), "headers": headers or []})


def test_canonical_pop_session_is_extracted_and_bearer_is_not() -> None:
    value, canonical = _extract_session_token(request("/x", [(b"authorization", b"PoP sess_safe")]))
    assert (value, canonical) == ("sess_safe", True)
    value, canonical = _extract_session_token(request("/x", [(b"authorization", b"Bearer unsafe")]))
    assert (value, canonical) == (None, False)


def test_query_order_is_bound_into_request_target() -> None:
    assert _canonical_request_target(request("/metrics?z=2&a=1")) == "/metrics?a=1&z=2"
    assert _canonical_request_target(request("/metrics?z=3&a=1")) != "/metrics?a=1&z=2"
