from app.schemas.offline_access import OfflinePackIssueRequest


def test_offline_schema_forbids_secret_material():
    fields = set(OfflinePackIssueRequest.model_fields)
    assert not fields & {
        "seed",
        "mnemonic",
        "xprv",
        "private_key",
        "session_token",
        "raw_access_pass",
        "lnurl_key",
        "k1",
    }
    assert OfflinePackIssueRequest.model_json_schema().get("additionalProperties") is False
