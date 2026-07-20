import json

import pytest

from app.services.lnurl.payer_data import (
    PayerDataAuthInvalidError,
    PayerDataInvalidJSONError,
    PayerDataTooLargeError,
    build_payer_data_declaration,
    parse_payerdata,
)


def valid_payload(k1: str) -> dict[str, dict[str, str]]:
    return {"auth": {"key": "02" + "11" * 32, "k1": k1, "sig": "3006020101020101"}}


def test_valid_auth_payerdata_accepted() -> None:
    k1 = "aa" * 32
    parsed = parse_payerdata(valid_payload(k1), require_auth=True)
    assert parsed.auth is not None
    assert parsed.auth.k1 == k1
    assert parsed.auth.key.startswith("02")
    assert parsed.payload_hash and parsed.payload_hash.startswith("sha256:")


def test_malformed_json_and_root_array_rejected() -> None:
    with pytest.raises(PayerDataInvalidJSONError):
        parse_payerdata("{")
    with pytest.raises(PayerDataInvalidJSONError):
        parse_payerdata(json.dumps([]))


def test_oversized_payerdata_rejected() -> None:
    with pytest.raises(PayerDataTooLargeError):
        parse_payerdata("{" + "a" * 5000 + "}", max_bytes=32)


@pytest.mark.parametrize(
    "payload",
    [
        {"auth": {"key": "04" + "11" * 64, "k1": "aa" * 32, "sig": "3006020101020101"}},
        {"auth": {"key": "02" + "11" * 32, "k1": "aa", "sig": "3006020101020101"}},
        {"auth": {"key": "02" + "11" * 32, "k1": "aa" * 32, "sig": "ff"}},
        {"auth": {"key": "02" + "11" * 32, "k1": "aa" * 32, "sig": "3006020101020101", "email": "x@example.com"}},
        {"email": "x@example.com"},
    ],
)
def test_invalid_auth_shapes_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(PayerDataAuthInvalidError):
        parse_payerdata(payload, require_auth=True)


def test_declaration_contains_only_auth_k1_and_mandatory() -> None:
    assert build_payer_data_declaration(k1="ab" * 32, mandatory=True) == {"auth": {"mandatory": True, "k1": "ab" * 32}}
