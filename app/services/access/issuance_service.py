"""Atomic device-bound proof verification and Access issuance (PI1)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session

from app.db.models.access import (
    AccessCheckoutSession,
    AccessDevice,
    AccessIssuedGrant,
    AccessIssuanceChallenge,
    AccessPaymentIntent,
)
from app.schemas.access_checkout import CheckoutStatus
from app.services.access.certificate_issuer import AccessCertificateIssuer
from app.services.access.crypto.hashing import (
    hash_canonical_json_prefixed,
    secure_nonce_hex,
)
from app.services.access.crypto.signatures import Ed25519SignatureSuite

PROTOCOL = "bastion-access-issuance-v1"
OPERATION = "access.issue"
SIGNING_CONTEXT = "access_challenge"


class AccessIssuanceError(ValueError):
    pass


class AccessIssuanceService:
    def __init__(self, db: Session, issuer: AccessCertificateIssuer, *, challenge_ttl_seconds: int = 300) -> None:
        self.db = db
        self.issuer = issuer
        self.challenge_ttl_seconds = challenge_ttl_seconds
        self.signatures = Ed25519SignatureSuite()

    def create_challenge(self, checkout_id: str, device_public_key: str) -> AccessIssuanceChallenge:
        checkout = self._eligible_checkout(checkout_id)
        fingerprint = self.signatures.public_key_fingerprint(device_public_key)
        now = datetime.now(UTC)
        payload = {
            "protocol": PROTOCOL,
            "operation": OPERATION,
            "checkout_id": checkout.id,
            "offer_revision_id": checkout.offer_revision_id,
            "capability": checkout.capability,
            "scopes": sorted(cast(list[str], checkout.scopes_json)),
            "terms_version": checkout.terms_version,
            "device_key_fingerprint": fingerprint,
            "nonce": secure_nonce_hex(32),
            "issued_at": _iso(now),
            "expires_at": _iso(now + timedelta(seconds=self.challenge_ttl_seconds)),
        }
        row = AccessIssuanceChallenge(
            id=f"access_challenge:{uuid4()}",
            checkout_id=checkout.id,
            device_public_key=device_public_key,
            device_key_fingerprint=fingerprint,
            payload_json=payload,
            payload_hash=hash_canonical_json_prefixed(payload),
            protocol_version=PROTOCOL,
            operation=OPERATION,
            status="pending",
            created_at=now,
            expires_at=now + timedelta(seconds=self.challenge_ttl_seconds),
        )
        self.db.add(row)
        self.db.flush()
        return row

    def verify_and_issue(self, checkout_id: str, challenge_id: str, signature: str) -> AccessIssuedGrant:
        existing = self.db.execute(
            select(AccessIssuedGrant).where(AccessIssuedGrant.checkout_id == checkout_id)
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        checkout = self._eligible_checkout(checkout_id)
        challenge = self.db.get(AccessIssuanceChallenge, challenge_id)
        if challenge is None or challenge.checkout_id != checkout.id:
            raise AccessIssuanceError("wrong_context")
        if challenge.operation != OPERATION or challenge.protocol_version != PROTOCOL:
            raise AccessIssuanceError("wrong_operation")
        if challenge.status != "pending" or challenge.consumed_at is not None:
            raise AccessIssuanceError("challenge_replayed")
        now = datetime.now(UTC)
        expires = challenge.expires_at.replace(tzinfo=UTC) if challenge.expires_at.tzinfo is None else challenge.expires_at
        if expires <= now:
            challenge.status = "expired"
            raise AccessIssuanceError("challenge_expired")
        result = self.signatures.verify(challenge.payload_json, SIGNING_CONTEXT, challenge.device_public_key, signature)
        if not result.valid:
            raise AccessIssuanceError("invalid_signature")
        claimed = cast(
            CursorResult[tuple[()]],
            self.db.execute(
                update(AccessIssuanceChallenge)
                .where(
                    AccessIssuanceChallenge.id == challenge.id,
                    AccessIssuanceChallenge.status == "pending",
                    AccessIssuanceChallenge.consumed_at.is_(None),
                )
                .values(status="processing")
            ),
        )
        if claimed.rowcount != 1:
            existing = self.db.execute(
                select(AccessIssuedGrant).where(AccessIssuedGrant.checkout_id == checkout_id)
            ).scalar_one_or_none()
            if existing is not None:
                return existing
            raise AccessIssuanceError("challenge_replayed")
        challenge.status = "processing"
        payment = self.db.get(AccessPaymentIntent, checkout.payment_intent_id)
        if payment is None:
            raise AccessIssuanceError("payment_missing")
        issued_at = now
        grant_expires_at = issued_at + timedelta(days=checkout.duration_days)
        certificate = self.issuer.issue_certificate_for_checkout(
            payment_intent=payment,
            device_public_key=challenge.device_public_key,
            device_key_fingerprint=challenge.device_key_fingerprint,
            scopes=list(cast(list[str], checkout.scopes_json)),
            expires_at=grant_expires_at,
        )
        self.db.add(AccessDevice(
            certificate_fingerprint=certificate.certificate_fingerprint,
            device_key_fingerprint=challenge.device_key_fingerprint,
            device_public_key=challenge.device_public_key,
            device_class="browser", status="active", first_seen_at=now,
            last_seen_at=now, risk_score=10, metadata_json={"registered_via": "checkout_issuance"},
            created_at=now, updated_at=now,
        ))
        grant = AccessIssuedGrant(
            id=f"access_grant:{uuid4()}", checkout_id=checkout.id,
            offer_revision_id=checkout.offer_revision_id,
            certificate_fingerprint=certificate.certificate_fingerprint,
            device_key_fingerprint=challenge.device_key_fingerprint,
            capability=checkout.capability,
            scopes_json=list(cast(list[str], checkout.scopes_json)),
            terms_version=checkout.terms_version, status="active",
            issued_at=issued_at, expires_at=grant_expires_at,
        )
        self.db.add(grant)
        challenge.status = "consumed"
        challenge.consumed_at = now
        checkout.status = CheckoutStatus.ISSUED.value
        self.db.flush()
        return grant

    def get_grant(self, grant_id: str) -> AccessIssuedGrant:
        grant = self.db.get(AccessIssuedGrant, grant_id)
        if grant is None:
            raise AccessIssuanceError("grant_not_found")
        return grant

    def canonical_payload(self, challenge: AccessIssuanceChallenge) -> str:
        return json.dumps(challenge.payload_json, sort_keys=True, separators=(",", ":"))

    def _eligible_checkout(self, checkout_id: str) -> AccessCheckoutSession:
        checkout = self.db.get(AccessCheckoutSession, checkout_id)
        if checkout is None:
            raise AccessIssuanceError("checkout_not_found")
        now = datetime.now(UTC).replace(tzinfo=None)
        expires = checkout.expires_at.replace(tzinfo=None) if checkout.expires_at.tzinfo else checkout.expires_at
        if expires <= now:
            checkout.status = CheckoutStatus.EXPIRED.value
            raise AccessIssuanceError("checkout_expired")
        if checkout.status != CheckoutStatus.ELIGIBLE.value:
            raise AccessIssuanceError("checkout_not_eligible")
        return checkout


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
