"""Declarative high-risk quorum policy providers; endpoints contain no quorum logic."""

from app.domain.wallet_auth.quorum import (
    QuorumParticipantSlot as Slot,
    QuorumParticipantType as P,
    QuorumPolicy,
    QuorumProofMethod as M,
    QuorumType,
)

WALLETS = frozenset({P.BITCOIN_WALLET_PRINCIPAL, P.LIGHTNING_WALLET_PRINCIPAL})
STRONG_WALLET_METHODS = frozenset({M.BIP322, M.HARDWARE_WALLET, M.AIR_GAPPED})
LEGACY_FORBIDDEN = frozenset({M.LEGACY_MESSAGE_SIGNATURE})


def business_owner_policy(action: str = "business_owner_change") -> QuorumPolicy:
    return QuorumPolicy(
        "business-owner-quorum-v1",
        1,
        QuorumType.BUSINESS,
        action,
        2,
        (
            Slot("owner", "business_owner", WALLETS, STRONG_WALLET_METHODS | {M.LNURL_AUTH}),
            Slot("admin", "business_admin", WALLETS, STRONG_WALLET_METHODS | {M.LNURL_AUTH}),
        ),
        2,
        1,
        WALLETS,
        STRONG_WALLET_METHODS | {M.LNURL_AUTH},
        LEGACY_FORBIDDEN,
        frozenset({"business_owner", "business_admin"}),
        expires_in_seconds=600,
        cooldown_seconds=300,
        metadata={"action_group": "business_roles"},
    )


def sovereign_recovery_policy() -> QuorumPolicy:
    methods = STRONG_WALLET_METHODS | {M.RECOVERY_CAPSULE, M.TRANSPARENCY_CHECKPOINT}
    return QuorumPolicy(
        "sovereign-recovery-quorum-v1",
        1,
        QuorumType.SOVEREIGN,
        "sovereign_recovery_complete",
        3,
        (
            Slot(
                "wallet_one",
                allowed_principal_types=WALLETS,
                allowed_proof_methods=STRONG_WALLET_METHODS,
            ),
            Slot(
                "wallet_two",
                allowed_principal_types=WALLETS,
                allowed_proof_methods=STRONG_WALLET_METHODS,
            ),
            Slot(
                "checkpoint",
                allowed_principal_types=frozenset({P.ISSUER_KEY}),
                allowed_proof_methods=frozenset({M.TRANSPARENCY_CHECKPOINT}),
                required_participant_type=P.TRANSPARENCY_CHECKPOINT,
            ),
        ),
        3,
        2,
        WALLETS | {P.ISSUER_KEY},
        methods,
        LEGACY_FORBIDDEN | {M.LNURL_AUTH},
        required_methods=frozenset({M.TRANSPARENCY_CHECKPOINT}),
        required_participant_types=frozenset({P.TRANSPARENCY_CHECKPOINT}),
        require_hardware_wallet=True,
        require_air_gapped_proof=True,
        require_recovery_capsule=True,
        require_transparency_checkpoint=True,
        expires_in_seconds=900,
        cooldown_seconds=172800,
        risk_level="sovereign",
        metadata={"action_group": "recovery"},
    )


def issuer_rotation_policy() -> QuorumPolicy:
    methods = frozenset(
        {M.HARDWARE_WALLET, M.AIR_GAPPED, M.ACCESS_CERTIFICATE, M.TRANSPARENCY_CHECKPOINT}
    )
    participants = frozenset(
        {
            P.BITCOIN_WALLET_PRINCIPAL,
            P.HARDWARE_WALLET,
            P.ACCESS_CERTIFICATE,
            P.ISSUER_KEY,
        }
    )
    return QuorumPolicy(
        "issuer-rotation-quorum-v1",
        1,
        QuorumType.ISSUER_ROTATION,
        "issuer_key_rotation",
        4,
        (
            Slot("owner", allowed_principal_types=participants, allowed_proof_methods=methods),
            Slot(
                "hardware",
                allowed_principal_types=participants,
                allowed_proof_methods=frozenset({M.HARDWARE_WALLET, M.AIR_GAPPED}),
                require_hardware_evidence=True,
            ),
            Slot(
                "certificate",
                allowed_principal_types=participants,
                allowed_proof_methods=frozenset({M.ACCESS_CERTIFICATE}),
                required_participant_type=P.ACCESS_CERTIFICATE,
            ),
            Slot(
                "checkpoint",
                allowed_principal_types=frozenset({P.ISSUER_KEY}),
                allowed_proof_methods=frozenset({M.TRANSPARENCY_CHECKPOINT}),
                required_participant_type=P.TRANSPARENCY_CHECKPOINT,
            ),
        ),
        4,
        4,
        participants,
        methods,
        LEGACY_FORBIDDEN | {M.LNURL_AUTH},
        required_methods=frozenset({M.ACCESS_CERTIFICATE, M.TRANSPARENCY_CHECKPOINT}),
        require_hardware_wallet=True,
        require_air_gapped_proof=True,
        require_transparency_checkpoint=True,
        expires_in_seconds=600,
        cooldown_seconds=86400,
        metadata={"action_group": "enterprise_policy"},
    )


__all__ = ["business_owner_policy", "issuer_rotation_policy", "sovereign_recovery_policy"]
