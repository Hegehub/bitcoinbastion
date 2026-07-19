from app.services.lnurl.payer_data import build_payer_data_declaration, parse_payerdata
from app.services.lnurl.payer_data_auth import PayerAuthChallengeStatus, PayerAuthChallenge
from datetime import UTC, datetime, timedelta


def test_declaration_requests_no_personal_fields_by_default() -> None:
    declaration = build_payer_data_declaration(k1="aa" * 32, mandatory=True)
    assert set(declaration) == {"auth"}
    assert "email" not in str(declaration).lower()
    assert "name" not in str(declaration).lower()
    assert "identifier" not in str(declaration).lower()


def test_raw_payerdata_not_in_parsed_safe_hashes() -> None:
    raw_key = "02" + "11" * 32
    raw_sig = "3006020101020101"
    parsed = parse_payerdata({"auth": {"key": raw_key, "k1": "aa" * 32, "sig": raw_sig}}, require_auth=True)
    dumped = str(parsed)
    assert raw_sig not in parsed.payload_hash
    assert raw_key not in parsed.payload_hash
    assert "wallet seed" not in dumped.lower()


def test_challenge_record_uses_hashed_lookup_fields() -> None:
    now = datetime.now(UTC)
    challenge = PayerAuthChallenge("id", "aa" * 32, "hmac-sha256:lookup", "req", None, "auth.bitcoin-bastion.com", "pro", "pro", None, None, "lnurl_payerdata_auth", PayerAuthChallengeStatus.UNUSED, now, now + timedelta(seconds=300))
    assert challenge.k1_hash.startswith("hmac-sha256:")
