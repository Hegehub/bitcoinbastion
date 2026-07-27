from app.services.access.principal_certificate_bridge import LegacyCertificateClass


def test_legacy_certificates_are_not_classified_as_principal_bound_by_default():
    assert LegacyCertificateClass.LEGACY_UNBOUND != LegacyCertificateClass.MIGRATED_PRINCIPAL_BOUND
    assert (
        LegacyCertificateClass.LEGACY_DEVICE_BOUND
        != LegacyCertificateClass.MIGRATED_PRINCIPAL_BOUND
    )
