from app.db.models.access import AccessCertificate, OfflineValidityPack, SubscriptionEntitlement


def test_issuer_metadata_columns_never_store_private_key_material():
    for model in (AccessCertificate, SubscriptionEntitlement, OfflineValidityPack):
        assert "private_key" not in model.__table__.columns
        assert "private_key_provider_reference" not in model.__table__.columns
