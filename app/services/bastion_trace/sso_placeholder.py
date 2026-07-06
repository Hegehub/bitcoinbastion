from app.schemas.bastion_trace import SsoConfigPlaceholder, SsoProviderType


def default_sso_config() -> SsoConfigPlaceholder:
    return SsoConfigPlaceholder(
        provider_type=SsoProviderType.UNCONFIGURED,
        configured=False,
        issuer_url=None,
        client_id_present=False,
        metadata_url_present=False,
        limitations=["SSO_NOT_CONFIGURED"],
    )
