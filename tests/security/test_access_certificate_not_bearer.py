from app.services.access.principal_certificate_bridge import PrincipalCertificateResult


def test_bridge_result_explicitly_requires_live_access_context():
    assert (
        "not_bearer_access"
        in PrincipalCertificateResult.__dataclass_fields__["limitations"].default
    )
