from bastion_ui.access_redaction import redact_sensitive_object


def test_principal_and_linking_material_are_not_rendered_raw() -> None:
    result = redact_sensitive_object(
        {"principal_hash": "hmac:raw", "lnurl_linking_key": "secret", "session_token": "sess"}
    )
    assert result["lnurl_linking_key"] == "<redacted>"
    assert result["session_token"] == "<redacted>"
