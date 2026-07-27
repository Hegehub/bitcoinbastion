from app.schemas.access import PrincipalAccessCertificateExportRequest


def test_export_schema_accepts_no_wallet_or_device_secret_material():
    fields = set(PrincipalAccessCertificateExportRequest.model_fields)
    assert fields == {"intent_signature_reference"}
    assert not fields & {"seed", "mnemonic", "xprv", "private_key", "session_token"}
