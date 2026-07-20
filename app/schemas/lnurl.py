"""Pydantic schemas for the Bastion LNURL adapter layer.

These schemas define request and response shapes only. They do not encode LNURLs,
verify signatures, issue invoices, settle payments, persist data, or authorize access.
"""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, Field, StrictInt, field_validator, model_validator

from app.domain.lnurl import (
    DEFAULT_ALLOWED_PAYERDATA_FIELDS,
    LIGHTNING_ADDRESS_NOT_IDENTITY_WARNING,
    LNURL_AUTH_ALLOWED_ACTIONS,
    LNURL_AUTH_STABLE_DOMAIN_WARNING,
    LNURL_INVOICE_NOT_SETTLED_WARNING,
    LNURL_K1_BYTES,
    LNURL_PAYERDATA_PRIVACY_WARNING,
    LNURL_WITHDRAW_AUTH_REQUIRED_WARNING,
    LNURLAuthAction,
    LNURLSuccessActionType,
)
from app.domain.wallet_auth import FORBIDDEN_WALLET_SECRET_TERMS, WalletPrincipalStatus, WalletRiskLevel, WalletVerificationStrength

FORBIDDEN_SUCCESS_ACTION_QUERY_TERMS = frozenset({"session_token", "access_pass", "recovery", "seed", "private_key"})
MAX_LNURL_COMMENT_LENGTH = 1_000
_COMPRESSED_SECP256K1_RE = re.compile(r"^(02|03)[0-9a-fA-F]{64}$")
_DER_SIGNATURE_RE = re.compile(r"^[0-9a-fA-F]{4,160}$")


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


def _validate_k1_hex(k1: str) -> str:
    if len(k1) != LNURL_K1_BYTES * 2:
        raise ValueError("LNURL k1 must be 32 bytes represented as hex.")
    try:
        bytes.fromhex(k1)
    except ValueError as exc:
        raise ValueError("LNURL k1 must be hex encoded.") from exc
    return k1


def _validate_success_action_url(url: str | None) -> str | None:
    if url is None:
        return None
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    lower_url = url.lower()
    for term in FORBIDDEN_SUCCESS_ACTION_QUERY_TERMS:
        if term in lower_url or term in query:
            raise ValueError("successAction URL contains unsafe secret-like material.")
    return url


class LNURLSchemaBase(BaseModel):
    model_config = {"extra": "forbid", "use_enum_values": False}


class LNURLAuthChallengeCreate(LNURLSchemaBase):
    action: LNURLAuthAction = Field(description="LNURL-auth action. LNURL-auth proves Lightning wallet control; protected API access still requires PoP session and Policy Engine.")
    origin: str = Field(min_length=1, description="Origin requesting LNURL-auth.")
    domain: str = Field(min_length=1, description=f"LNURL-auth domain. {LNURL_AUTH_STABLE_DOMAIN_WARNING}")
    device_key_fingerprint: str | None = Field(default=None, description="Optional device key fingerprint for later device binding.")
    requested_scopes: list[str] = Field(default_factory=list, description="Requested scopes; final authorization belongs to Policy Engine.")
    requested_metric_groups: list[str] = Field(default_factory=list, description="Requested metric groups.")
    risk_level: WalletRiskLevel | None = Field(default=None, description="Risk hint only.")
    policy_intent_hash: str | None = Field(default=None, description="Optional policy intent hash bound to the k1 challenge.")
    callback_base_url: str | None = Field(default=None, description="Optional callback base URL.")
    metadata: dict[str, Any] | None = Field(default=None, description="Bastion will never ask for a Bitcoin seed or private key.")

    @field_validator("action")
    @classmethod
    def validate_action(cls, action: LNURLAuthAction) -> LNURLAuthAction:
        if action not in LNURL_AUTH_ALLOWED_ACTIONS:
            raise ValueError("Unsupported LNURL-auth action.")
        return action

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        return _validate_safe_metadata(metadata)


class LNURLAuthChallengeResponse(LNURLSchemaBase):
    challenge_id: str = Field(description="Opaque LNURL-auth challenge id.")
    k1: str = Field(description="Single-use 32-byte LNURL k1 challenge; expires quickly and must not be logged raw.")
    action: LNURLAuthAction = Field(description="External LNURL-auth action.")
    callback_url: str = Field(description="LNURL-auth callback URL.")
    lnurl_bech32: str = Field(description="LNURL bech32 payload created by a later encoder.")
    domain: str = Field(description="Domain bound to k1.")
    expires_at: datetime = Field(description="k1 expiry timestamp.")
    device_key_fingerprint: str | None = None
    policy_intent_hash: str | None = None
    security_warning: str = Field(default="LNURL-auth proves Lightning wallet control; protected API access still requires PoP session and Policy Engine.")
    cors_required: bool = True

    @field_validator("k1")
    @classmethod
    def validate_k1(cls, k1: str) -> str:
        return _validate_k1_hex(k1)


class LNURLAuthCallbackRequest(LNURLSchemaBase):
    k1: str = Field(description="Single-use LNURL-auth k1. Signature verification happens in service layer.")
    key: str = Field(description="Compressed secp256k1 public key from wallet; never treated as legal identity.")
    sig: str = Field(description="DER-encoded ECDSA signature; schema does not verify cryptography.")
    action: LNURLAuthAction | None = Field(default=None, description="Optional action echoed by wallet/client.")

    @field_validator("k1")
    @classmethod
    def validate_k1(cls, k1: str) -> str:
        return _validate_k1_hex(k1.lower())

    @field_validator("key")
    @classmethod
    def validate_key(cls, key: str) -> str:
        if _COMPRESSED_SECP256K1_RE.fullmatch(key) is None:
            raise ValueError("LNURL-auth key must be a compressed secp256k1 public key in hex.")
        return key.lower()

    @field_validator("sig")
    @classmethod
    def validate_sig(cls, sig: str) -> str:
        if _DER_SIGNATURE_RE.fullmatch(sig) is None:
            raise ValueError("LNURL-auth signature must be bounded DER hex.")
        return sig.lower()


class LNURLAuthCallbackResponse(LNURLSchemaBase):
    status: str
    reason: str | None = None

    @classmethod
    def ok(cls) -> "LNURLAuthCallbackResponse":
        return cls(status="OK")

    @classmethod
    def error(cls) -> "LNURLAuthCallbackResponse":
        return cls(status="ERROR", reason="Authentication request could not be verified.")


class LightningPrincipalResponse(LNURLSchemaBase):
    principal_hash: str = Field(description="Privacy-preserving Lightning Principal hash; no user_id.")
    lnurl_key_hash: str = Field(description="HMAC/hash of LNURL key; no raw key.")
    auth_domain: str = Field(description="LNURL-auth domain for domain-specific linking key.")
    proof_method: str = Field(default="lnurl_auth")
    verification_strength: WalletVerificationStrength
    status: WalletPrincipalStatus
    created_at: datetime
    last_verified_at: datetime | None = None
    per_product_alias: str | None = Field(default=None, description="Optional per-product pseudonym; no legal identity or email required.")


class LNURLPaySubscriptionCreate(LNURLSchemaBase):
    plan_code: str = Field(description="Subscription plan code.")
    amount_msat: int | None = Field(default=None, gt=0, description="Requested amount in millisatoshis, if fixed.")
    currency: str | None = Field(default="BTC")
    duration_days: int | None = Field(default=None, gt=0)
    principal_hash: str | None = Field(default=None, description="Optional principal binding; not email identity.")
    payerdata_auth_requested: bool = Field(default=False, description="Request payerData.auth instead of mandatory personal identity.")
    success_action_requested: bool = Field(default=True)
    comment_allowed: StrictInt | None = Field(default=None, ge=0, le=MAX_LNURL_COMMENT_LENGTH, description="Comment length allowance; untrusted metadata only, never authorization or identity.")
    metadata: dict[str, Any] | None = Field(default=None, description=f"{LNURL_INVOICE_NOT_SETTLED_WARNING} payerData.email is not mandatory.")

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        return _validate_safe_metadata(metadata)


class LNURLPayRequestResponse(LNURLSchemaBase):
    tag: str = Field(default="payRequest", description="LNURL-pay tag.")
    callback: str = Field(description="LNURL-pay callback URL.")
    min_sendable: int = Field(gt=0, description="Minimum sendable amount in msat.")
    max_sendable: int = Field(gt=0, description="Maximum sendable amount in msat.")
    metadata: str = Field(description="JSON-encoded LNURL-pay metadata string; must include text/plain metadata later.")
    comment_allowed: StrictInt | None = Field(default=None, ge=0, le=MAX_LNURL_COMMENT_LENGTH, description="Untrusted comment length allowance; not authorization.")
    payer_data: dict[str, Any] | None = Field(default=None, description=f"{LNURL_PAYERDATA_PRIVACY_WARNING} Defaults allow only {DEFAULT_ALLOWED_PAYERDATA_FIELDS}.")
    allows_nostr: bool | None = None
    nostr_pubkey: str | None = None

    @model_validator(mode="after")
    def validate_sendable_range(self) -> "LNURLPayRequestResponse":
        if self.min_sendable > self.max_sendable:
            raise ValueError("min_sendable must be less than or equal to max_sendable.")
        return self


class LNURLPayCallbackRequest(LNURLSchemaBase):
    payment_id: str
    amount: int = Field(gt=0, description="Amount in msat requested by wallet.")
    comment: str | None = Field(default=None, max_length=MAX_LNURL_COMMENT_LENGTH, description="Untrusted user metadata; cannot authorize access, identity, settlement, refund, or entitlement.")
    payerdata: dict[str, Any] | None = Field(default=None, description="payerData.auth may be present; email/name are not required.")
    nostr: str | None = None

    @field_validator("payerdata")
    @classmethod
    def validate_payerdata(cls, payerdata: dict[str, Any] | None) -> dict[str, Any] | None:
        return _validate_safe_metadata(payerdata)




class LNURLValidatedCommentMetadata(LNURLSchemaBase):
    present: bool
    normalized_comment: str | None = Field(default=None, exclude=True, description="Internal normalized comment; not public API output by default.")
    comment_hash: str | None = Field(default=None, description="Hash-only commitment; raw comments are not exposed.")
    character_count: int = Field(ge=0)
    allowed_character_count: int = Field(ge=0)
    storage_mode: str = Field(description="none, hash_only, or encrypted.")
    classification: str = Field(description="Deterministic untrusted metadata classification.")
    input_trust: str = Field(default="untrusted_external_metadata")
    suspicious_text_flags: list[str] = Field(default_factory=list)


class LNURLSuccessAction(LNURLSchemaBase):
    tag: str = Field(description="successAction tag: message or url.")
    message: str | None = None
    description: str | None = None
    url: str | None = Field(default=None, description="Short-lived activation URL only; must not contain raw pass/session/recovery/private data.")

    @field_validator("tag")
    @classmethod
    def validate_tag(cls, tag: str) -> str:
        allowed = {LNURLSuccessActionType.MESSAGE.value, LNURLSuccessActionType.URL.value}
        if tag not in allowed:
            raise ValueError("Unsupported successAction tag.")
        return tag

    @field_validator("url")
    @classmethod
    def validate_url(cls, url: str | None) -> str | None:
        return _validate_success_action_url(url)


class LNURLPayCallbackResponse(LNURLSchemaBase):
    pr: str = Field(description="BOLT-11 invoice. Invoice issuance is not settlement.")
    routes: list[Any] = Field(default_factory=list)
    verify: str | None = Field(default=None, description="Optional verify URL.")
    success_action: dict[str, Any] | None = Field(default=None, description="successAction must not contain raw session/pass/recovery data.")
    disposable: bool | None = None

    @field_validator("success_action")
    @classmethod
    def validate_success_action(cls, success_action: dict[str, Any] | None) -> dict[str, Any] | None:
        if success_action and "url" in success_action:
            _validate_success_action_url(str(success_action["url"]))
        return success_action


class LNURLVerifyResponse(LNURLSchemaBase):
    settled: bool = Field(description="settled=false must not issue entitlement.")
    preimage: str | None = Field(default=None, description="May be omitted when unavailable.")
    pr: str | None = None
    payment_hash: str | None = None
    verified_at: datetime | None = None
    audit_event_hash: str | None = None


class LNURLPaymentProofResponse(LNURLSchemaBase):
    payment_proof_hash: str
    payment_hash: str
    invoice_hash: str
    lnurl_callback_hash: str
    principal_hash: str | None = None
    plan_code: str | None = None
    amount_msat: int = Field(gt=0)
    settled: bool
    settled_at: datetime | None = None
    verify_method: str
    audit_event_hash: str | None = None


class LNURLPayerDataRequest(LNURLSchemaBase):
    name: dict[str, Any] | None = Field(default=None, description="Optional and disabled by default; not mandatory identity.")
    pubkey: dict[str, Any] | None = None
    identifier: dict[str, Any] | None = Field(default=None, description="Must not become global user_id.")
    email: dict[str, Any] | None = Field(default=None, description="Optional and disabled by default; email is not mandatory.")
    auth: dict[str, Any] | None = Field(default=None, description="Preferred payerData field for payment-auth binding.")


class LNURLPayerDataReceived(LNURLSchemaBase):
    payerdata_hash: str
    auth_present: bool = False
    pubkey_present: bool = False
    identifier_present: bool = False
    email_present: bool = False
    redacted_summary: dict[str, Any]
    retention_policy: str | None = None


class LightningAddressResponse(LNURLSchemaBase):
    username: str
    domain: str
    address: str = Field(description=f"{LIGHTNING_ADDRESS_NOT_IDENTITY_WARNING} It must not become user_id.")
    lnurl_pay: LNURLPayRequestResponse
    product_code: str | None = None
    merchant_id_hash: str | None = None
    terminal_id_hash: str | None = None


class LNURLWithdrawRequestCreate(LNURLSchemaBase):
    principal_hash: str | None = None
    amount_msat: int = Field(gt=0)
    reason: str = Field(description="Withdraw reason; no wallet secrets.")
    payout_type: str = Field(description="Withdraw purpose or payout type.")
    policy_context: dict[str, Any] | None = Field(default=None, description=f"{LNURL_WITHDRAW_AUTH_REQUIRED_WARNING}")
    step_up_id: str | None = None

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, reason: str) -> str:
        if _contains_forbidden_secret_terms(reason):
            raise ValueError("Withdraw reason contains forbidden wallet secret terms.")
        return reason

    @field_validator("policy_context")
    @classmethod
    def validate_policy_context(cls, policy_context: dict[str, Any] | None) -> dict[str, Any] | None:
        return _validate_safe_metadata(policy_context)


class LNURLWithdrawRequestResponse(LNURLSchemaBase):
    tag: str = Field(default="withdrawRequest")
    callback: str
    k1: str = Field(description="Single-use 32-byte withdraw k1; expires quickly.")
    default_description: str
    min_withdrawable: int = Field(gt=0)
    max_withdrawable: int = Field(gt=0)
    expires_at: datetime
    policy_approved: bool = Field(description="Must be true for valuable payouts before QR issuance.")
    audit_event_hash: str | None = None

    @field_validator("k1")
    @classmethod
    def validate_k1(cls, k1: str) -> str:
        return _validate_k1_hex(k1)

    @model_validator(mode="after")
    def validate_withdrawable_range(self) -> "LNURLWithdrawRequestResponse":
        if self.min_withdrawable > self.max_withdrawable:
            raise ValueError("min_withdrawable must be less than or equal to max_withdrawable.")
        return self


class LNURLWithdrawCallbackRequest(LNURLSchemaBase):
    withdraw_id: str
    k1: str
    pr: str = Field(description="Wallet-provided BOLT-11 invoice; service layer verifies k1 and policy state.")

    @field_validator("k1")
    @classmethod
    def validate_k1(cls, k1: str) -> str:
        return _validate_k1_hex(k1)


class LNURLWithdrawCallbackResponse(LNURLSchemaBase):
    status: str
    reason: str | None = None
    payout_id_hash: str | None = None
    audit_event_hash: str | None = None


class LNURLReceiptPacketResponse(LNURLSchemaBase):
    receipt_hash: str
    payment_proof_hash: str
    invoice_hash: str
    metadata_hash: str
    entitlement_hash: str | None = None
    audit_event_hash: str
    issued_at: datetime
    payregister_context_hash: str | None = None


class LNURLSecurityStatusResponse(LNURLSchemaBase):
    k1_status: str
    domain_valid: bool
    action_allowed: bool
    replay_detected: bool
    verification_strength: WalletVerificationStrength | None = None
    policy_required: bool
    policy_decision: str | None = None
    audit_required: bool = True

class LNURLPayerAuthDeclaration(LNURLSchemaBase):
    mandatory: bool = Field(description="Whether payerData.auth is required for this payment request.")
    k1: str = Field(description="64-character payerData.auth challenge; not a login credential.")

    @field_validator("k1")
    @classmethod
    def validate_payer_auth_k1(cls, k1: str) -> str:
        return _validate_k1_hex(k1.lower())


class LNURLPayerAuthPayload(LNURLSchemaBase):
    key: str = Field(description="Compressed secp256k1 LNURL linking key. It is hashed before persistence.")
    k1: str = Field(description="Single-use payerData.auth challenge.")
    sig: str = Field(description="DER-encoded ECDSA signature over k1.")

    @field_validator("key")
    @classmethod
    def validate_payer_auth_key(cls, key: str) -> str:
        if _COMPRESSED_SECP256K1_RE.fullmatch(key) is None:
            raise ValueError("payerData.auth key must be compressed secp256k1 hex.")
        return key.lower()

    @field_validator("k1")
    @classmethod
    def validate_payer_auth_payload_k1(cls, k1: str) -> str:
        return _validate_k1_hex(k1.lower())

    @field_validator("sig")
    @classmethod
    def validate_payer_auth_sig(cls, sig: str) -> str:
        if _DER_SIGNATURE_RE.fullmatch(sig) is None:
            raise ValueError("payerData.auth signature must be bounded DER hex.")
        return sig.lower()


class LNURLPayerDataPayload(LNURLSchemaBase):
    auth: LNURLPayerAuthPayload | None = Field(default=None, description="Only auth is supported by default; email/name/identifier are not accepted.")


class LNURLPaymentPrincipalBinding(LNURLSchemaBase):
    payment_request_id: str
    principal_hash: str
    principal_type: str = Field(default="lightning_wallet_principal")
    product_pseudonym: str
    auth_method: str = Field(default="lnurl_payerdata_auth")
    verification_strength: str = Field(default="standard")
    settled: bool = Field(default=False, description="payerData.auth is not settlement; this remains false until verifier confirms payment.")

class LNURLPayDiscoveryResponse(LNURLSchemaBase):
    callback: str = Field(description="Trusted absolute LNURL-pay callback URL. Discovery does not create an invoice or prove payment.")
    max_sendable: StrictInt = Field(alias="maxSendable", ge=1, description="Maximum sendable amount in millisatoshis.")
    min_sendable: StrictInt = Field(alias="minSendable", ge=1, description="Minimum sendable amount in millisatoshis.")
    metadata: str = Field(description="JSON-serialized LNURL-pay metadata array containing text/plain and text/identifier entries.")
    tag: str = Field(default="payRequest", description="LNURL-pay discovery tag; this endpoint does not authenticate or authorize users.")
    comment_allowed: StrictInt | None = Field(default=None, alias="commentAllowed", ge=0, description="Optional LUD-12 comment character allowance in untrusted metadata.")
    payer_data: dict[str, Any] | None = Field(default=None, alias="payerData", description="Optional LUD-18 payerData policy; not identity or settlement.")

    @model_validator(mode="after")
    def validate_amounts_and_tag(self) -> "LNURLPayDiscoveryResponse":
        if self.tag != "payRequest":
            raise ValueError("LNURL-pay discovery tag must be payRequest.")
        if self.max_sendable < self.min_sendable:
            raise ValueError("maxSendable must be greater than or equal to minSendable.")
        return self


class LNURLErrorResponse(LNURLSchemaBase):
    status: str = Field(default="ERROR", description="LNURL protocol error status.")
    reason: str = Field(description="Generic wallet-safe error reason.")
