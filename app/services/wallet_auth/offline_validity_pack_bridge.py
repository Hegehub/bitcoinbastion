"""Wallet/LNURL principal adapter for the canonical Access offline-pack issuer."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.wallet_auth import WalletDevice, WalletPrincipal
from app.services.access.offline_validity_pack import (
    OfflinePackError,
    OfflinePackIssueRequest,
    OfflinePackIssueResult,
    OfflineValidityPackService,
)


class WalletOfflineValidityPackBridge:
    def __init__(self, db: Session, service: OfflineValidityPackService) -> None:
        self.db, self.service = db, service

    def issue(self, request: OfflinePackIssueRequest) -> OfflinePackIssueResult:
        principal = self.db.execute(
            select(WalletPrincipal)
            .where(WalletPrincipal.principal_hash == request.principal_hash)
            .with_for_update()
        ).scalar_one_or_none()
        if principal is None or principal.status != "active" or principal.revoked_at:
            raise OfflinePackError("principal_revoked")
        device = self.db.execute(
            select(WalletDevice)
            .where(
                WalletDevice.principal_hash == request.principal_hash,
                WalletDevice.device_key_fingerprint == request.device_key_fingerprint,
            )
            .with_for_update()
        ).scalar_one_or_none()
        if device is None or device.status != "active" or device.revoked_at:
            raise OfflinePackError("device_revoked")
        if principal.principal_type != request.principal_type:
            raise OfflinePackError("principal_mismatch")
        # LNURL control is continuity evidence, never on-chain treasury authority.
        if (
            request.principal_type == "lightning_wallet_principal"
            and request.proof_method != "lnurl_auth"
        ):
            raise OfflinePackError("proof_too_weak")
        return self.service.issue_pack(request)


__all__ = ["WalletOfflineValidityPackBridge"]
