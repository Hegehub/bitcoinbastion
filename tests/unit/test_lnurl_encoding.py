import pytest

from app.services.lnurl.encoding import _bech32_encode, _convertbits, _encode_bech32m_for_test, decode_lnurl, encode_lnurl
from app.services.lnurl.errors import (
    LNURLDecodingError,
    LNURLInputTooLargeError,
    LNURLInvalidChecksumError,
    LNURLInvalidHRPError,
    LNURLInvalidUTF8Error,
    LNURLMixedCaseError,
    LNURLUnsafeURLError,
)
from app.services.lnurl.url_safety import LNURLURLPolicy, MAX_LNURL_VALUE_CHARS

POLICY = LNURLURLPolicy.remote_fetch()


def test_valid_https_url_round_trip_and_lowercase() -> None:
    url = "https://example.com/lnurl/callback?tag=login&k1=abc"
    encoded = encode_lnurl(url, policy=POLICY)
    assert encoded.startswith("lnurl1")
    assert encoded == encoded.lower()
    decoded = decode_lnurl(encoded, policy=POLICY)
    assert decoded.normalized_url == url
    assert decoded.hostname == "example.com"
    assert decoded.has_query is True
    assert "k1=abc" not in repr(decoded)


def test_uppercase_and_lightning_prefix_are_accepted() -> None:
    encoded = encode_lnurl("https://example.com/a", policy=POLICY)
    assert decode_lnurl(encoded.upper(), policy=POLICY).normalized_url == "https://example.com/a"
    assert decode_lnurl(f"lightning:{encoded.upper()}", policy=POLICY).hostname == "example.com"


def test_mixed_case_wrong_hrp_invalid_checksum_and_bech32m_rejected() -> None:
    encoded = encode_lnurl("https://example.com/a", policy=POLICY)
    with pytest.raises(LNURLMixedCaseError):
        decode_lnurl(encoded[:6].upper() + encoded[6:], policy=POLICY)
    wrong_hrp = "lnoops" + encoded[len("lnurl"):]
    with pytest.raises(LNURLInvalidChecksumError):
        decode_lnurl(wrong_hrp, policy=POLICY)
    wrong_hrp_valid_checksum = _bech32_encode("oops", [1, 2, 3])
    with pytest.raises(LNURLInvalidHRPError):
        decode_lnurl(wrong_hrp_valid_checksum, policy=POLICY)
    with pytest.raises(LNURLInvalidChecksumError):
        decode_lnurl(_encode_bech32m_for_test("https://example.com/a"), policy=POLICY)


def test_invalid_padding_utf8_nul_crlf_empty_and_size_limits() -> None:
    invalid_padding = _bech32_encode("lnurl", [16])
    with pytest.raises(LNURLDecodingError):
        decode_lnurl(invalid_padding, policy=POLICY)
    bad_utf8 = _bech32_encode("lnurl", _convertbits(b"\xff", 8, 5, True))
    with pytest.raises(LNURLInvalidUTF8Error):
        decode_lnurl(bad_utf8, policy=POLICY)
    nul = _bech32_encode("lnurl", [0, 0])
    with pytest.raises(LNURLInvalidUTF8Error):
        decode_lnurl(nul, policy=POLICY)
    with pytest.raises(LNURLDecodingError):
        decode_lnurl("", policy=POLICY)
    with pytest.raises(LNURLInputTooLargeError):
        decode_lnurl("lnurl1" + "q" * (MAX_LNURL_VALUE_CHARS + 20), policy=POLICY)


def test_invalid_url_after_decoding_is_rejected_and_oversized_url_not_encoded() -> None:
    encoded_http = encode_lnurl("http://localhost:8000/a", policy=LNURLURLPolicy.development(ports=(8000,)))
    with pytest.raises(LNURLUnsafeURLError):
        decode_lnurl(encoded_http, policy=POLICY)
    with pytest.raises(LNURLUnsafeURLError):
        encode_lnurl("http://example.com/a", policy=POLICY)
