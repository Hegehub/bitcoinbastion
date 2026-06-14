from __future__ import annotations

import httpx

from bitcoin_bastion_sdk.transport import unwrap_response


def test_unwraps_response_envelope_data() -> None:
    response = httpx.Response(200, json={"data": {"value": 1}, "error": None, "meta": {}})
    assert unwrap_response(response) == {"value": 1}


def test_supports_raw_true() -> None:
    payload = {"data": {"value": 1}, "error": None, "meta": {"request_id": "r1"}}
    response = httpx.Response(200, json=payload)
    assert unwrap_response(response, raw=True) == payload


def test_handles_plain_dict_response() -> None:
    response = httpx.Response(200, json={"status": "ok"})
    assert unwrap_response(response) == {"status": "ok"}
