"""
Service layer for the Bastion access layer.

These classes outline the responsibilities of the payment, certificate
and session services. They do not perform actual network calls or
cryptographic operations; instead they define the method signatures and
document the expected behaviour. Concrete implementations should be
provided by integrators to handle Lightning invoices, BTCPay integration,
hash derivation, signature verification and secure session handling.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Optional
import secrets

from .models import PaymentProof, AccessCertificate, ApiEntitlements, SubscriptionEntitlement, AccessSession
from .policy import PolicyEngine, PolicyDecision


class PaymentService:
    """
    Handles creation and verification of payment proofs.

    In a full implementation this service would interact with Lightning or
    on‑chain payment processors to generate invoices and verify payment receipts.
    """

    def create_payment_intent(self, amount: int, tier: str) -> PaymentProof:
        """
        Create a new payment intent. Returns a PaymentProof with a pending status.
        The `payment_id_hash` and `invoice_hash` must be derived using a secure
        HMAC with a server pepper.
        """
        timestamp = datetime.utcnow()
        # Placeholder identifiers (should be HMAC of real IDs).
        payment_id_hash = secrets.token_hex(16)
        invoice_hash = secrets.token_hex(16)
        return PaymentProof(
            payment_id_hash=payment_id_hash,
            invoice_hash=invoice_hash,
            amount=amount,
            status="pending",
            timestamp=timestamp,
            product_tier=tier,
        )

    def mark_paid(self, proof: PaymentProof) -> PaymentProof:
        """Mark an existing PaymentProof as paid."""
        return proof.copy(update={"status": "paid"})


class CertificateService:
    """
    Issues and manages access certificates and subscription entitlements.
    """

    def issue_certificate(
        self,
        proof: PaymentProof,
        device_public_keys: Dict[str, str],
        tier: str,
        subscription: Optional[SubscriptionEntitlement] = None,
        scopes: Optional[list[str]] = None,
    ) -> AccessCertificate:
        """
        Issue a new access certificate bound to the provided device keys and tier.

        The `pass_commitment` and `pass_lookup_hash` should be derived from a
        unique pass identifier using HMAC‑SHA256. Here we generate random
        identifiers as placeholders.
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(days=365)
        pass_commitment = secrets.token_hex(16)
        pass_lookup_hash = secrets.token_hex(16)
        certificate_fingerprint = secrets.token_hex(16)
        api_entitlements = None
        if subscription is not None:
            # Derive default API entitlements from the subscription plan.
            # In a real system this mapping would be configured.
            api_entitlements = ApiEntitlements(
                metric_groups=[],
                max_history_days=0,
                min_interval="1h",
                websocket_streams=0,
                batch_query=False,
                child_api_keys=0,
            )
        return AccessCertificate(
            pass_commitment=pass_commitment,
            pass_lookup_hash=pass_lookup_hash,
            certificate_fingerprint=certificate_fingerprint,
            tier=tier,
            public_keys=device_public_keys,
            scopes=scopes or [],
            subscription=subscription,
            api_entitlements=api_entitlements,
            issued_at=now,
            expires_at=expires_at,
            issuer_signatures={"classical": {"alg": "Ed25519", "sig": ""}},
        )


class SessionService:
    """
    Manages proof‑of‑possession sessions.

    Sessions are short‑lived and require clients to sign each API request.
    """

    def create_session(
        self, certificate: AccessCertificate, scopes: list[str], duration_minutes: int = 120
    ) -> AccessSession:
        """
        Create a new session associated with the access certificate. In a real
        implementation this would also generate a session keypair and return
        a token to the client.
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=duration_minutes)
        session_id = secrets.token_hex(16)
        session_token = secrets.token_hex(32)
        session_key_fingerprint = secrets.token_hex(16)
        return AccessSession(
            session_id=session_id,
            session_token=session_token,
            session_key_fingerprint=session_key_fingerprint,
            scopes=scopes,
            created_at=now,
            expires_at=expires_at,
        )

    def validate_request(
        self, session: AccessSession, scope: str, policy_engine: Optional[PolicyEngine] = None
    ) -> PolicyDecision:
        """
        Validate that a request using the given session is allowed. This stub
        uses an optional PolicyEngine to check the scope; additional checks
        (nonce reuse, signature verification, quota enforcement) must be added.
        """
        engine = policy_engine or PolicyEngine()
        # Basic expiry check
        if session.expires_at < datetime.utcnow():
            return PolicyDecision.DENY
        if scope not in session.scopes:
            return PolicyDecision.DENY
        # Defer to policy engine to decide
        # Note: in a real implementation we would also pass the subscription and
        # certificate to the engine.
        dummy_certificate = AccessCertificate(
            pass_commitment="",
            pass_lookup_hash="",
            certificate_fingerprint="",
            tier="",
            public_keys={},
            scopes=session.scopes,
            subscription=None,
            api_entitlements=None,
            issued_at=session.created_at,
            expires_at=session.expires_at,
            issuer_signatures={},
        )
        return engine.evaluate_request(dummy_certificate, scope)
