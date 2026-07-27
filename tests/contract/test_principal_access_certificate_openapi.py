from app.schemas.access import PrincipalAccessCertificateIssueRequest


def test_principal_certificate_request_contract_has_no_secret_fields():
    schema = PrincipalAccessCertificateIssueRequest.model_json_schema()
    fields = set(schema["properties"])
    assert {"principal_type", "device_binding_reference", "requested_scopes"} <= fields
    assert not fields & {"seed", "mnemonic", "xprv", "private_key", "raw_access_pass"}
    assert schema.get("additionalProperties") is False
