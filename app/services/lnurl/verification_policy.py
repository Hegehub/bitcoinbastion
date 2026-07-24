"""Declarative LNURL settlement verification policy."""

from __future__ import annotations
from dataclasses import dataclass
from app.services.lnurl.verification_sources import (
    LNURLVerificationConfidence,
    LNURLVerificationSourceType,
)


@dataclass(frozen=True, slots=True)
class LNURLVerificationPolicy:
    allow_remote_only_lite: bool = True
    require_remote_preimage: bool = True
    allow_manual_source: bool = False
    environment: str = "production"

    def source_allowed(self, source: LNURLVerificationSourceType) -> bool:
        return source is not LNURLVerificationSourceType.MANUAL_TEST_SOURCE or (
            self.allow_manual_source and self.environment != "production"
        )

    def confidence_allowed(
        self,
        *,
        plan_code: str | None,
        confidence: LNURLVerificationConfidence,
        preimage_verified: bool,
    ) -> bool:
        plan = (plan_code or "").lower()
        if confidence in {
            LNURLVerificationConfidence.INTERNALLY_CONFIRMED,
            LNURLVerificationConfidence.PROVIDER_CONFIRMED,
            LNURLVerificationConfidence.DUAL_CONFIRMED,
        }:
            return True
        if confidence is not LNURLVerificationConfidence.REMOTE_ONLY:
            return False
        if plan in {
            "business",
            "business_pass",
            "enterprise",
            "enterprise_pass",
            "payregister",
            "payregister_payment",
        }:
            return False
        return self.allow_remote_only_lite and (
            preimage_verified or not self.require_remote_preimage
        )
