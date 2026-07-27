from app.services.access.revocation_registry import RevocationTargetType


def test_certificate_binding_revocation_targets_are_authoritative():
    assert (
        RevocationTargetType.CERTIFICATE_PRINCIPAL_BINDING.value == "certificate_principal_binding"
    )
    assert RevocationTargetType.CERTIFICATE_DEVICE_BINDING.value == "certificate_device_binding"
    assert (
        RevocationTargetType.CERTIFICATE_ENTITLEMENT_BINDING.value
        == "certificate_entitlement_binding"
    )
