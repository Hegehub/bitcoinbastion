"""Stable transparency checkpoint taxonomy and source constraints."""

from enum import StrEnum


class TransparencyCheckpointType(StrEnum):
    ISSUER_KEY_EPOCH = "issuer_key_epoch"
    POLICY_EPOCH = "policy_epoch"
    POLICY_BUNDLE_ROOT = "policy_bundle_root"
    REVOCATION_EPOCH = "revocation_epoch"
    WALLET_AUTH_SCHEMA_EPOCH = "wallet_auth_schema_epoch"
    LNURL_AUTH_DOMAIN_EPOCH = "lnurl_auth_domain_epoch"
    WALLET_CREDENTIAL_BATCH_ROOT = "wallet_credential_batch_root"
    LIGHTNING_PRINCIPAL_BATCH_ROOT = "lightning_principal_batch_root"
    SUBSCRIPTION_ENTITLEMENT_BATCH_ROOT = "subscription_entitlement_batch_root"
    ACCESS_CERTIFICATE_BATCH_ROOT = "access_certificate_batch_root"
    DELEGATED_PASS_BATCH_ROOT = "delegated_pass_batch_root"
    CHILD_API_KEY_BATCH_ROOT = "child_api_key_batch_root"
    RECOVERY_EVENT_ROOT = "recovery_event_root"
    RECOVERY_CAPSULE_EPOCH = "recovery_capsule_epoch"
    QUORUM_POLICY_EPOCH = "quorum_policy_epoch"
    OFFLINE_VALIDITY_PACK_EPOCH = "offline_validity_pack_epoch"
    LNURL_PAYMENT_PROOF_BATCH_ROOT = "lnurl_payment_proof_batch_root"
    LNURL_WITHDRAW_BATCH_ROOT = "lnurl_withdraw_batch_root"
    LIGHTNING_ADDRESS_REGISTRY_ROOT = "lightning_address_registry_root"
    WALLET_COMPATIBILITY_REGISTRY_ROOT = "wallet_compatibility_registry_root"
    AUDIT_CHAIN_CHECKPOINT = "audit_chain_checkpoint"
    EMERGENCY_LOCKDOWN_CHECKPOINT = "emergency_lockdown_checkpoint"


class TransparencyVisibility(StrEnum):
    PUBLIC_SAFE = "public_safe"
    OPERATOR = "operator"
    RESTRICTED = "restricted"
    RECOVERY_QUORUM_ONLY = "recovery_quorum_only"


class PublicationStatus(StrEnum):
    INTERNAL = "internal"
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    VALID = "valid"
    INVALID = "invalid"
    INCOMPLETE = "incomplete"


PUBLIC_SAFE_TYPES = frozenset(
    {
        TransparencyCheckpointType.ISSUER_KEY_EPOCH,
        TransparencyCheckpointType.POLICY_EPOCH,
        TransparencyCheckpointType.POLICY_BUNDLE_ROOT,
        TransparencyCheckpointType.REVOCATION_EPOCH,
        TransparencyCheckpointType.WALLET_AUTH_SCHEMA_EPOCH,
        TransparencyCheckpointType.LNURL_AUTH_DOMAIN_EPOCH,
        TransparencyCheckpointType.WALLET_COMPATIBILITY_REGISTRY_ROOT,
        TransparencyCheckpointType.AUDIT_CHAIN_CHECKPOINT,
    }
)

# A builder accepts only these normalized leaf classes for each stream. Unknown
# source classes never become eligible merely because their strings look valid.
PERMITTED_LEAF_TYPES: dict[TransparencyCheckpointType, frozenset[str]] = {
    checkpoint_type: frozenset({checkpoint_type.value.removesuffix("_root").removesuffix("_epoch")})
    for checkpoint_type in TransparencyCheckpointType
}
PERMITTED_LEAF_TYPES.update(
    {
        TransparencyCheckpointType.POLICY_BUNDLE_ROOT: frozenset({"policy_bundle"}),
        TransparencyCheckpointType.WALLET_CREDENTIAL_BATCH_ROOT: frozenset(
            {"wallet_credential", "device_binding", "wallet_step_up"}
        ),
        TransparencyCheckpointType.RECOVERY_EVENT_ROOT: frozenset({"recovery_event"}),
        TransparencyCheckpointType.LNURL_PAYMENT_PROOF_BATCH_ROOT: frozenset(
            {"lnurl_payment_proof"}
        ),
    }
)


def default_visibility(checkpoint_type: TransparencyCheckpointType | str) -> TransparencyVisibility:
    try:
        parsed = TransparencyCheckpointType(checkpoint_type)
    except ValueError:
        return TransparencyVisibility.RESTRICTED
    return (
        TransparencyVisibility.PUBLIC_SAFE
        if parsed in PUBLIC_SAFE_TYPES
        else TransparencyVisibility.RESTRICTED
    )
