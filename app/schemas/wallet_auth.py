"""Pydantic schemas for Wallet-first Proof-of-Access Auth PQ v2.

These schemas define request and response shapes only. They do not verify wallet
signatures, issue sessions, persist data, or make authorization decisions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.wallet_auth import (
    DEDICATED_AUTH_ADDRESS_WARNING,
    FORBIDDEN_WALLET_SECRET_TERMS,
    REQUIRED_SIGNATURE_WARNING,
    WALLET_AUTH_INTENT_TYPE,
    WALLET_AUTH_INTENT_VERSION,
    CRITICAL_WALLET_ACTIONS,
    WalletAuthAction,
    WalletDeviceClass,
    WalletDeviceStatus,
    WalletNetwork,
    WalletPrincipalActorType,
    WalletPrincipalStatus,
    WalletProofType,
    WalletRecoveryProfile,
    WalletRiskLevel,
    WalletVerificationStrength,
)

FORBIDDEN_BROAD_SCOPES = frozenset({"api:all", "metrics:all", "admin:all"})
SECRET_FIELD_DESCRIPTION = "Bastion will never ask for a Bitcoin seed or private key."


def _contains_forbidden_secret_terms(value: Any) -> bool:
    text = str(value).lower()
    return any(term.lower() in text for term in FORBIDDEN_WALLET_SECRET_TERMS)


def _validate_safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if metadata is None:
        return None
    for key, value in metadata.items():
        if _contains_forbidden_secret_terms(key) or _contains_forbidden_secret_terms(value):
            raise ValueError("Metadata contains forbidden wallet secret terms.")
    return metadata


def _validate_requested_scopes(scopes: list[str]) -> list[str]:
    if FORBIDDEN_BROAD_SCOPES.intersection(scopes):
        raise ValueError("Broad wallet auth scopes are not allowed in schema requests.")
    return scopes


class WalletSchemaBase(BaseModel):
    model_config = {"extra": "forbid", "use_enum_values": False}


class WalletAuthChallengeCreate(WalletSchemaBase):
    action: WalletAuthAction = Field(description="Wallet auth action. Wallet proof proves control; it does not grant full access by itself.")
    network: WalletNetwork | None = Field(default=None, description="Bitcoin network for wallet proof. Mainnet, testnet, signet and regtest are not interchangeable.")
    origin: str = Field(min_length=1, description="Origin requesting the challenge.")
    device_key_fingerprint: str | None = Field(default=None, description="Optional device key fingerprint for device continuity.")
    requested_scopes: list[str] = Field(default_factory=list, description="Requested scopes; broad scopes such as api:all are rejected.")
    requested_metric_groups: list[str] = Field(default_factory=list, description="Requested metric entitlement groups.")
    risk_level: WalletRiskLevel | None = Field(default=None, description="Risk hint only; Policy Engine makes final access decision.")
    use_lnurl: bool = Field(default=False, description="Request LNURL-auth as Lightning-native proof; LNURL-auth is not full authorization.")
    use_bip322: bool = Field(default=True, description="Request BIP-322 as preferred Bitcoin ownership proof.")
    require_hardware_wallet: bool = Field(default=False, description="Request hardware-wallet flow; hardware claims are not assurance without later verification.")
    metadata: dict[str, Any] | None = Field(default=None, description=SECRET_FIELD_DESCRIPTION)

    @field_validator("requested_scopes")
    @classmethod
    def validate_requested_scopes(cls, scopes: list[str]) -> list[str]:
        return _validate_requested_scopes(scopes)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        return _validate_safe_metadata(metadata)

    @model_validator(mode="after")
    def validate_critical_risk(self) -> "WalletAuthChallengeCreate":
        if self.action in CRITICAL_WALLET_ACTIONS and self.risk_level is WalletRiskLevel.LOW:
            raise ValueError("Critical wallet actions cannot be requested with low risk level.")
        return self


class WalletAuthChallengeResponse(WalletSchemaBase):
    challenge_id: str = Field(description="Opaque challenge identifier.")
    intent_type: str = Field(default=WALLET_AUTH_INTENT_TYPE, description="Structured Bastion wallet auth intent type.")
    intent_version: int = Field(default=WALLET_AUTH_INTENT_VERSION, description="Structured intent version.")
    canonical_intent: str = Field(description="Canonical intent users sign. This signature does not authorize a Bitcoin transaction.")
    intent_hash: str = Field(description="Hash of canonical intent.")
    network: WalletNetwork | None = Field(default=None, description="Network the challenge is bound to.")
    action: WalletAuthAction = Field(description="Wallet auth action bound to the intent.")
    origin: str = Field(description="Origin bound to the intent.")
    nonce: str = Field(description="Challenge nonce.")
    expires_at: datetime = Field(description="Challenge expiry timestamp.")
    device_key_fingerprint: str | None = Field(default=None, description="Optional device key fingerprint.")
    policy_hash: str | None = Field(default=None, description="Optional policy hash; not server pepper or internal lookup hash.")
    risk_level: WalletRiskLevel = Field(description="Risk hint for the challenge.")
    signature_warning: str = Field(default=REQUIRED_SIGNATURE_WARNING, description="Must warn that this signature does not authorize a Bitcoin transaction.")
    dedicated_auth_address_warning: str = Field(default=DEDICATED_AUTH_ADDRESS_WARNING, description="Use a dedicated Bastion auth wallet/address.")
    lnurl_auth_url: str | None = Field(default=None, description="Optional LNURL-auth URL for Lightning-native auth.")
    lnurl_auth_bech32: str | None = Field(default=None, description="Optional bech32 LNURL-auth payload.")


class WalletRegisterRequest(WalletSchemaBase):
    challenge_id: str = Field(description="Challenge being answered.")
    proof_type: WalletProofType = Field(description="Wallet proof type; verification happens in service layer.")
    wallet_identifier: str | None = Field(default=None, description="Wallet proof input such as a Bitcoin address; never returned as identity.")
    signature: str = Field(description="Wallet signature proof input; not stored or returned raw by response schemas.")
    public_key: str | None = Field(default=None, description="Optional wallet public key proof input.")
    device_key_fingerprint: str = Field(description="Device key fingerprint for continuity.")
    device_class: WalletDeviceClass = Field(description="Device class requesting registration.")
    origin: str = Field(min_length=1, description="Origin bound to registration.")
    network: WalletNetwork | None = Field(default=None, description="Bitcoin network for the proof.")
    wallet_name: str | None = Field(default=None, description="Optional local display name; not identity.")
    hardware_wallet_claim: dict[str, Any] | None = Field(default=None, description="Client-supplied hardware metadata; not high assurance without verification.")

    @field_validator("hardware_wallet_claim")
    @classmethod
    def validate_hardware_wallet_claim(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        return _validate_safe_metadata(metadata)


class WalletLoginRequest(WalletSchemaBase):
    challenge_id: str = Field(description="Login challenge being answered.")
    proof_type: WalletProofType = Field(description="Wallet proof type; login returns PoP session response, not bearer token response.")
    wallet_identifier: str | None = Field(default=None, description="Wallet proof input only; not public identity.")
    signature: str = Field(description="Wallet signature proof input.")
    public_key: str | None = Field(default=None, description="Optional wallet public key proof input.")
    device_key_fingerprint: str = Field(description="Device key fingerprint for continuity.")
    origin: str = Field(min_length=1, description="Origin bound to login.")
    network: WalletNetwork | None = Field(default=None, description="Bitcoin network for proof.")


class WalletPrincipalResponse(WalletSchemaBase):
    principal_hash: str = Field(description="Privacy-preserving principal identifier; no global user_id.")
    principal_type: str = Field(description="Principal type label.")
    actor_type: WalletPrincipalActorType = Field(description="Policy actor type.")
    status: WalletPrincipalStatus = Field(description="Principal lifecycle status.")
    verification_strength: WalletVerificationStrength = Field(description="Verified proof strength.")
    network: WalletNetwork | None = Field(default=None, description="Wallet network if applicable.")
    proof_method: WalletProofType = Field(description="Proof method used for verification.")
    address_hash: str | None = Field(default=None, description="HMAC/hash of wallet address; no raw address in response.")
    script_pubkey_hash: str | None = Field(default=None, description="HMAC/hash of scriptPubKey; no raw script identity.")
    lnurl_key_hash: str | None = Field(default=None, description="HMAC/hash of LNURL key; no raw key in response.")
    auth_domain: str | None = Field(default=None, description="LNURL-auth domain if applicable.")
    created_at: datetime = Field(description="Creation timestamp.")
    last_verified_at: datetime | None = Field(default=None, description="Last verification timestamp.")
    dedicated_auth_address_recommended: bool = Field(default=True, description="Use a dedicated Bastion auth wallet/address.")


class WalletDeviceBindRequest(WalletSchemaBase):
    principal_hash: str = Field(description="Principal hash to bind the device to.")
    device_key_fingerprint: str = Field(description="Device key fingerprint.")
    device_class: WalletDeviceClass = Field(description="Device class. Browser extension is not root of trust for critical binding.")
    binding_method: str = Field(description="Binding method name.")
    challenge_id: str | None = Field(default=None, description="Optional challenge id used for binding.")
    step_up_id: str | None = Field(default=None, description="Optional step-up id used for binding.")
    metadata: dict[str, Any] | None = Field(default=None, description=SECRET_FIELD_DESCRIPTION)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        return _validate_safe_metadata(metadata)

    @model_validator(mode="after")
    def validate_browser_extension_binding(self) -> "WalletDeviceBindRequest":
        if self.device_class is WalletDeviceClass.BROWSER_EXTENSION and self.binding_method == "root_of_trust":
            raise ValueError("Browser extension cannot be submitted as root of trust for critical binding.")
        return self


class WalletDeviceResponse(WalletSchemaBase):
    device_id_hash: str
    principal_hash: str
    device_key_fingerprint: str
    device_class: WalletDeviceClass
    status: WalletDeviceStatus
    risk_score: int | None = Field(default=None, ge=0, le=100)
    binding_method: str
    created_at: datetime
    last_seen_at: datetime | None = None
    can_approve_critical_actions: bool


class WalletSessionCreate(WalletSchemaBase):
    principal_hash: str = Field(description="Principal requesting a PoP-oriented session.")
    device_key_fingerprint: str = Field(description="Device key fingerprint for session binding.")
    challenge_id: str = Field(description="Challenge id used for session creation.")
    signed_challenge: str = Field(description="Signed challenge proof; no wallet seeds or private keys are accepted.")
    requested_scopes: list[str] = Field(default_factory=list, description="Requested scopes for PoP session.")
    requested_metric_groups: list[str] = Field(default_factory=list, description="Requested metric groups for PoP session.")

    @field_validator("requested_scopes")
    @classmethod
    def validate_requested_scopes(cls, scopes: list[str]) -> list[str]:
        return _validate_requested_scopes(scopes)


class WalletSessionResponse(WalletSchemaBase):
    session_token: str = Field(description="Returned once for PoP session creation; not a bearer Access Pass. Protected requests still require request signature and Policy Engine.")
    session_type: str = Field(default="pop", description="Proof-of-Possession session type.")
    principal_hash: str
    device_key_fingerprint: str
    scopes: list[str]
    metric_groups: list[str]
    expires_at: datetime
    issued_at: datetime
    policy_mode: str = Field(description="Policy mode for protected requests.")
    requires_request_signature: bool = Field(default=True, description="Protected requests must still use request signatures.")


class WalletPoPRequestHeaders(WalletSchemaBase):
    authorization: str = Field(description="PoP sess_... authorization header; this is not bearer auth.")
    bastion_request_timestamp: str = Field(description="X-Bastion timestamp for request freshness.")
    bastion_request_nonce: str = Field(description="X-Bastion nonce for replay prevention.")
    bastion_request_body_hash: str = Field(description="X-Bastion body hash.")
    bastion_request_signature: str = Field(description="X-Bastion request signature.")
    bastion_principal: str = Field(description="Principal hash used for request context.")


class WalletStepUpRequest(WalletSchemaBase):
    action: WalletAuthAction = Field(description="Action requiring step-up.")
    principal_hash: str
    device_key_fingerprint: str
    requested_scopes: list[str] = Field(default_factory=list)
    requested_metric_groups: list[str] = Field(default_factory=list)
    intent_hash: str | None = None
    risk_level: WalletRiskLevel = Field(description="Risk hint; Policy Engine decides final action.")
    challenge_id: str | None = None
    proof_type: WalletProofType = Field(description="Allows BIP-322 and LNURL-auth step-up flows; strength enforced by service/policy.")
    signature: str | None = Field(default=None, description="Optional wallet signature proof input.")
    lnurl_auth_attempt_id: str | None = Field(default=None, description="Optional LNURL-auth step-up attempt id.")

    @field_validator("requested_scopes")
    @classmethod
    def validate_requested_scopes(cls, scopes: list[str]) -> list[str]:
        return _validate_requested_scopes(scopes)


class WalletStepUpResponse(WalletSchemaBase):
    step_up_id: str
    principal_hash: str
    action: WalletAuthAction
    verified: bool
    verification_strength: WalletVerificationStrength
    expires_at: datetime
    policy_decision: str
    audit_event_hash: str | None = None


class WalletEntitlementResponse(WalletSchemaBase):
    principal_hash: str = Field(description="Entitlement is bound to principal, not email or user_id.")
    actor_type: WalletPrincipalActorType
    plan_code: str
    status: str
    scopes: list[str]
    metric_groups: list[str]
    limits: dict[str, Any]
    valid_from: datetime
    valid_until: datetime
    issuer_signature_fingerprint: str | None = None
    crypto_epoch: int | None = None


class WalletRecoveryStartRequest(WalletSchemaBase):
    principal_hash: str
    recovery_profile: WalletRecoveryProfile
    requested_action: str = Field(default="recovery_start")
    proof_type: WalletProofType | None = None
    lnurl_auth_requested: bool = Field(default=False, description="LNURL-auth may be requested as one factor, not sole high-value recovery.")
    reason: str | None = Field(default=None, description=SECRET_FIELD_DESCRIPTION)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, reason: str | None) -> str | None:
        if reason is not None and _contains_forbidden_secret_terms(reason):
            raise ValueError("Recovery reason contains forbidden wallet secret terms.")
        return reason


class WalletRecoveryCompleteRequest(WalletSchemaBase):
    recovery_attempt_id: str
    principal_hash: str
    factors: list[dict[str, Any]] = Field(description="Recovery factors. Service layer enforces profile-specific quorum.")
    step_up_id: str | None = None
    cooldown_acknowledged: bool

    @field_validator("factors")
    @classmethod
    def validate_factors(cls, factors: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for factor in factors:
            _validate_safe_metadata(factor)
        return factors


class WalletRecoveryStatusResponse(WalletSchemaBase):
    recovery_attempt_id: str
    principal_hash: str
    status: str
    required_factors: list[str]
    completed_factors: list[str]
    cooldown_until: datetime | None = None
    audit_event_hash: str | None = None


class WalletLNURLRecoveryFactorResponse(WalletSchemaBase):
    """LNURL-auth satisfies one factor and never returns an authenticated session."""

    type: str = "bastion_lnurl_recovery_factor"
    recovery_attempt_id: str = Field(description="Opaque recovery attempt reference.")
    lnurl: str = Field(description="Short-lived recovery-specific LNURL-auth URI.")
    qr_payload: str = Field(description="QR payload equivalent to lnurl.")
    expires_at: datetime
    factor_status: str
    remaining_factor_count: int = Field(ge=1)
    warning: str = Field(description="LNURL-auth proof satisfies one Recovery Capsule factor. It does not complete recovery by itself.")


class WalletQuorumApprovalView(WalletSchemaBase):
    approval_hash: str = Field(description="Commitment to a verified approval; never a raw proof.")
    participant_type: str
    proof_method: str
    slot_id: str
    role: str | None = None
    verification_strength: str
    expires_at: datetime


class WalletQuorumStatusResponse(WalletSchemaBase):
    quorum_hash: str = Field(description="Opaque HMAC-derived quorum reference.")
    quorum_type: str
    action: str
    status: str
    decision: str
    threshold: int = Field(ge=1)
    approval_count: int = Field(ge=0)
    distinct_principals: int = Field(ge=0)
    distinct_methods: int = Field(ge=0)
    filled_slots: list[str]
    missing_roles: list[str]
    missing_methods: list[str]
    cooldown_until: datetime | None = None
    policy_hash: str
    warning: str = Field(
        default="A quorum coordinates distributed authority. It does not bypass the Policy Engine, scopes, entitlements, revocation, or active PoP Session requirements."
    )


class WalletLockdownRequest(WalletSchemaBase):
    principal_hash: str
    reason: str
    step_up_id: str | None = None
    signed_intent: str | None = None

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, reason: str) -> str:
        if _contains_forbidden_secret_terms(reason):
            raise ValueError("Lockdown reason contains forbidden wallet secret terms.")
        return reason


class WalletLockdownResponse(WalletSchemaBase):
    principal_hash: str
    lockdown_id: str
    status: str
    frozen_sessions: int = Field(ge=0)
    revoked_child_keys: int = Field(ge=0)
    audit_event_hash: str | None = None
    recovery_required: bool
