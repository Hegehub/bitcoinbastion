from app.services.access.offline_validity_pack import OfflinePackIssueRequest


def test_wallet_request_has_no_raw_wallet_or_lnurl_key_fields():
    fields = set(OfflinePackIssueRequest.__dataclass_fields__)
    assert not fields & {
        "wallet_address",
        "lnurl_linking_key",
        "k1",
        "signature",
        "seed",
        "private_key",
    }
