from app.services.access.audit_chain import AccessAuditEventType
from app.services.access.principal_certificate_bridge import SUPPORTED_PRINCIPAL_TYPES
from app.services.access.revocation_registry import RevocationTargetType


def test_principal_certificate_flow_has_policy_bound_lifecycle_integrations():
    assert "bitcoin_wallet_principal" in SUPPORTED_PRINCIPAL_TYPES
    assert "lightning_wallet_principal" in SUPPORTED_PRINCIPAL_TYPES
    assert AccessAuditEventType.PRINCIPAL_CERTIFICATE_ISSUED.value == "principal_certificate_issued"
    assert RevocationTargetType.ACCESS_CERTIFICATE.value == "access_certificate"
    assert RevocationTargetType.CERTIFICATE_PRINCIPAL_BINDING.value == "certificate_principal_binding"
