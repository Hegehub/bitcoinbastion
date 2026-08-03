from cli.bastion_cli.output import redact


def test_lnurl_and_session_material_redacted():
    value = redact(
        {
            "k1": "raw-k1",
            "signature": "raw-sig",
            "session_token": "sess",
            "device_private_key": "dev",
            "preimage": "pre",
            "recovery_material": "rec",
        }
    )
    assert all(item == "[REDACTED]" for item in value.values())
