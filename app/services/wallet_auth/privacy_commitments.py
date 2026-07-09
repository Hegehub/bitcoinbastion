"""Privacy-preserving commitments for Wallet-first + LNURL auth.

These helpers produce lookup hashes, non-secret commitments, redacted debug
strings, and validation guards. They do not verify Bitcoin signatures, LNURL
callbacks, payments, policy decisions, audit events, or revocation state.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from app.services.access.crypto.hashing import hmac_sha256_prefixed, sha256_prefixed

_ALLOWED_PAYERDATA_ALWAYS = {"auth", "pubkey"}
_PERSONAL_PAYERDATA_FIELDS = {"email", "name"}
_OPTIONAL_PAYERDATA_FIELDS = {"identifier"}
_FORBIDDEN_SECRET_TERMS = (
    "seed phrase",
    "wallet seed",
    "bitcoin seed",
    "mnemonic",
    "private_key",
    "private key",
    "raw private key",
    "xprv",
    "yprv",
    "zprv",
)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")
_HEX_LIKE_RE = re.compile(r"^[0-9a-fA-F]+$")


class WalletPrivacyCommitmentError(ValueError):
    """Safe privacy commitment validation error that never includes raw input."""


def _to_bytes(value: str | bytes, field_name: str) -> bytes:
    if isinstance(value, bytes):
        result = value
    elif isinstance(value, str):
        result = value.encode("utf-8")
    else:
        raise TypeError(f"{field_name} must be str or bytes")
    if result == b"":
        raise ValueError(f"{field_name} must not be empty")
    return result


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


def compute_hmac_lookup_hash(server_pepper: str | bytes, namespace: str, value: str | bytes) -> str:
    """Return an HMAC-SHA256 lookup hash with explicit namespace separation."""

    pepper_bytes = _to_bytes(server_pepper, "server_pepper")
    namespace_text = _require_text(namespace, "namespace")
    value_bytes = _to_bytes(value, "value")
    payload = namespace_text.encode("utf-8") + b"\x00" + value_bytes
    return hmac_sha256_prefixed(pepper_bytes, payload)


def compute_sha256_commitment(value: str | bytes) -> str:
    """Return a SHA-256 commitment for non-lookup proof material."""

    value_bytes = _to_bytes(value, "value")
    return sha256_prefixed(value_bytes)


def canonicalize_identifier(value: str) -> str:
    """Trim an identifier without destructive protocol-specific lowercasing."""

    return _require_text(value, "identifier")


def compute_wallet_principal_hash(
    server_pepper: str | bytes,
    wallet_identifier: str,
    network: str,
    product_context: str | None = None,
) -> str:
    identifier = canonicalize_identifier(wallet_identifier)
    network_text = _require_text(network, "network")
    namespace = "wallet_principal"
    if product_context is not None:
        namespace = f"{namespace}:{_require_text(product_context, 'product_context')}"
    return compute_hmac_lookup_hash(server_pepper, namespace, f"{network_text}\x00{identifier}")


def compute_address_lookup_hash(server_pepper: str | bytes, address: str, network: str) -> str:
    address_text = canonicalize_identifier(address)
    network_text = _require_text(network, "network")
    return compute_hmac_lookup_hash(server_pepper, "bitcoin_address", f"{network_text}\x00{address_text}")


def compute_script_pubkey_commitment(script_pubkey_hex: str) -> str:
    script_text = _require_text(script_pubkey_hex, "script_pubkey_hex")
    if len(script_text) % 2 != 0 or _HEX_LIKE_RE.fullmatch(script_text) is None:
        raise ValueError("script_pubkey_hex must be a non-empty hex-like string")
    return compute_sha256_commitment(f"script_pubkey\x00{script_text.lower()}")


def compute_wallet_proof_hash(proof_material: str | bytes, proof_type: str) -> str:
    proof_type_text = _require_text(proof_type, "proof_type")
    proof_bytes = _to_bytes(proof_material, "proof_material")
    return compute_sha256_commitment(proof_type_text.encode("utf-8") + b"\x00" + proof_bytes)


def compute_lightning_principal_hash(
    server_pepper: str | bytes,
    lnurl_key: str,
    auth_domain: str,
    product_context: str | None = None,
) -> str:
    key_text = canonicalize_identifier(lnurl_key)
    domain_text = _require_text(auth_domain, "auth_domain")
    namespace = "lightning_principal"
    if product_context is not None:
        namespace = f"{namespace}:{_require_text(product_context, 'product_context')}"
    return compute_hmac_lookup_hash(server_pepper, namespace, f"{domain_text}\x00{key_text}")


def compute_lnurl_key_hash(server_pepper: str | bytes, lnurl_key: str, auth_domain: str) -> str:
    key_text = canonicalize_identifier(lnurl_key)
    domain_text = _require_text(auth_domain, "auth_domain")
    return compute_hmac_lookup_hash(server_pepper, "lnurl_key", f"{domain_text}\x00{key_text}")


def compute_lnurl_k1_hash(k1: str | bytes) -> str:
    return compute_sha256_commitment(_to_bytes(k1, "k1"))


def compute_lnurl_callback_hash(callback_url: str) -> str:
    callback_text = _require_text(callback_url, "callback_url")
    redacted_url = _redact_url_query_values(callback_text)
    return compute_sha256_commitment(f"lnurl_callback\x00{redacted_url}")


def compute_lightning_address_hash(
    server_pepper: str | bytes,
    lightning_address: str,
    product_context: str | None = None,
) -> str:
    local_part, domain = parse_lightning_address_parts(lightning_address)
    namespace = "lightning_address"
    if product_context is not None:
        namespace = f"{namespace}:{_require_text(product_context, 'product_context')}"
    return compute_hmac_lookup_hash(server_pepper, namespace, f"{local_part}\x00{domain}")


def parse_lightning_address_parts(lightning_address: str) -> tuple[str, str]:
    address = canonicalize_identifier(lightning_address)
    if address.count("@") != 1:
        raise ValueError("lightning_address must contain exactly one @")
    local_part, domain = address.split("@", 1)
    if not local_part or not domain:
        raise ValueError("lightning_address local-part and domain must not be empty")
    return local_part, domain


def compute_lnurl_payment_request_hash(payment_request_id: str, plan_code: str | None = None) -> str:
    request_id = _require_text(payment_request_id, "payment_request_id")
    plan = _require_text(plan_code, "plan_code") if plan_code is not None else ""
    return compute_sha256_commitment(f"lnurl_payment_request\x00{plan}\x00{request_id}")


def compute_lnurl_invoice_hash(bolt11_invoice: str) -> str:
    invoice = _require_text(bolt11_invoice, "bolt11_invoice")
    return compute_sha256_commitment(f"bolt11_invoice\x00{invoice}")


def compute_lnurl_payment_proof_hash(payment_hash: str, invoice_hash: str, settled_at: str | None = None) -> str:
    payment = _require_text(payment_hash, "payment_hash")
    invoice = _require_text(invoice_hash, "invoice_hash")
    settled = _require_text(settled_at, "settled_at") if settled_at is not None else "unsettled"
    return compute_sha256_commitment(f"lnurl_payment_proof\x00{payment}\x00{invoice}\x00{settled}")


def compute_payerdata_hash(server_pepper: str | bytes, payerdata: dict[Any, Any]) -> str:
    if not isinstance(payerdata, dict) or not payerdata:
        raise ValueError("payerdata must be a non-empty dict")
    canonical = json.dumps(payerdata, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return compute_hmac_lookup_hash(server_pepper, "payerdata", canonical)


def filter_allowed_payerdata_fields(payerdata: dict[Any, Any], allow_personal_fields: bool = False) -> dict[str, Any]:
    if not isinstance(payerdata, dict):
        raise TypeError("payerdata must be a dict")
    allowed: set[str] = set(_ALLOWED_PAYERDATA_ALWAYS)
    if allow_personal_fields:
        allowed.update(_PERSONAL_PAYERDATA_FIELDS)
        allowed.update(_OPTIONAL_PAYERDATA_FIELDS)
    return {str(key): value for key, value in payerdata.items() if str(key) in allowed}


def sanitize_lnurl_comment(comment: str, max_length: int) -> str:
    if max_length < 0:
        raise ValueError("max_length must be non-negative")
    text = _require_text(comment, "comment")
    text = _CONTROL_CHARS_RE.sub("", text).strip()
    return text[:max_length]


def build_safe_success_action_reference(server_pepper: str | bytes, payment_id: str, purpose: str) -> str:
    payment = _require_text(payment_id, "payment_id")
    purpose_text = _require_text(purpose, "purpose")
    digest = compute_hmac_lookup_hash(server_pepper, "success_action", f"{purpose_text}\x00{payment}")
    digest_hex = digest.split(":", 1)[1]
    token = base64.urlsafe_b64encode(bytes.fromhex(digest_hex[:32])).decode("ascii").rstrip("=")
    return f"act_{token}"


def compute_product_pseudonym(server_pepper: str | bytes, principal_hash: str, product_context: str) -> str:
    principal = _require_text(principal_hash, "principal_hash")
    product = _require_text(product_context, "product_context")
    return compute_hmac_lookup_hash(server_pepper, f"product_pseudonym:{product}", principal)


def redact_wallet_identifier(value: str) -> str:
    return _redact_with_label("wallet", value)


def redact_lnurl_identifier(value: str) -> str:
    return _redact_with_label("lnurl", value)


def redact_lightning_address(value: str) -> str:
    try:
        local_part, domain = parse_lightning_address_parts(value)
    except ValueError:
        return _redact_with_label("lightning-address", value)
    return f"lightning-address:{_edge(local_part)}@{_edge(domain)}"


def redact_bolt11_invoice(value: str) -> str:
    return _redact_with_label("bolt11", value)


def redact_sensitive_auth_material(value: str) -> str:
    text = str(value)
    lower = text.lower()
    if "@" in text:
        return redact_lightning_address(text)
    if lower.startswith("lnbc") or lower.startswith("lntb") or lower.startswith("lnbcrt"):
        return redact_bolt11_invoice(text)
    if lower.startswith("lnurl"):
        return redact_lnurl_identifier(text)
    if any(term in lower for term in _FORBIDDEN_SECRET_TERMS) or lower.startswith(("xprv", "yprv", "zprv")):
        return _redact_with_label("secret", text)
    return _redact_with_label("auth", text)


def reject_forbidden_wallet_secret_input(value: str, field_name: str) -> None:
    field = _require_text(field_name, "field_name")
    text = _require_text(value, "value")
    lowered = f"{field} {text}".lower()
    if any(term in lowered for term in _FORBIDDEN_SECRET_TERMS) or lowered.startswith(("xprv", "yprv", "zprv")):
        raise WalletPrivacyCommitmentError(f"Forbidden wallet secret material in field {field!r}")


def assert_no_global_user_id(field_name: str, value: str) -> None:
    field = _require_text(field_name, "field_name")
    _require_text(value, "value")
    if field == "user_id":
        raise WalletPrivacyCommitmentError("Wallet/LNURL identity must use principal_hash or product_pseudonym, not user_id")


@dataclass(frozen=True)
class PrivacyCommitmentContext:
    server_pepper: str
    product_context: str | None = None
    auth_domain: str | None = None
    network: str | None = None
    retention_policy: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.server_pepper, "server_pepper")

    def __repr__(self) -> str:
        return (
            "PrivacyCommitmentContext("
            "server_pepper='<redacted>', "
            f"product_context={self.product_context!r}, "
            f"auth_domain={self.auth_domain!r}, "
            f"network={self.network!r}, "
            f"retention_policy={self.retention_policy!r})"
        )


def _redact_url_query_values(url: str) -> str:
    parts = urlsplit(url)
    redacted_query = "&".join(
        f"{item.split('=', 1)[0]}=<redacted>" if "=" in item else "<redacted>" for item in parts.query.split("&") if item
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, redacted_query, ""))


def _redact_with_label(label: str, value: str) -> str:
    text = str(value)
    if text == "":
        return f"{label}:<empty>"
    return f"{label}:{_edge(text)}:{compute_sha256_commitment(text)[7:15]}"


def _edge(value: str) -> str:
    if len(value) <= 6:
        return "<redacted>"
    return f"{value[:3]}...{value[-3:]}"
