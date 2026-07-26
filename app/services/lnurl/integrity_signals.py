"""LNURL-auth and settlement signals using commitments and verified flags only."""

from __future__ import annotations

from datetime import datetime

from app.domain.access.integrity import AccessIntegrityRecommendation as R
from app.domain.access.integrity import AccessIntegritySignal as Signal
from app.domain.access.integrity import AccessIntegritySignalCategory as C
from app.domain.access.integrity import AccessIntegritySignalStatus as S


def collect_lnurl_signals(
    evidence: dict[str, object], now: datetime, maximum_points: int = 10
) -> list[Signal]:
    if evidence.get("lnurl_not_applicable"):
        return [
            Signal(
                "lnurl-auth",
                C.LNURL_AUTH,
                S.NOT_APPLICABLE,
                0,
                maximum_points,
                "lnurl_not_applicable",
                "LNURL-auth is not configured for this actor.",
                observed_at=now,
            )
        ]
    status, points, code, cap = S.UNAVAILABLE, 0.0, "lnurl_auth_unavailable", None
    if evidence.get("lnurl_k1_reused"):
        status, code, cap = S.UNSAFE, "lnurl_k1_reused", 20
    elif evidence.get("lnurl_domain_mismatch"):
        status, code, cap = S.UNSAFE, "lnurl_domain_mismatch", 20
    elif (
        evidence.get("lnurl_signature_valid")
        and evidence.get("lnurl_k1_consumed")
        and evidence.get("lnurl_action_matched")
    ):
        status, points, code = S.HEALTHY, float(maximum_points), "lnurl_auth_verified"
    elif evidence.get("lnurl_k1_expired"):
        status, points, code = S.DEGRADED, maximum_points * 0.2, "lnurl_k1_expired"
    elif evidence.get("lnurl_signature_valid") is False:
        status, code = S.UNSAFE, "lnurl_signature_invalid"
    return [
        Signal(
            "lnurl-auth",
            C.LNURL_AUTH,
            status,
            points,
            maximum_points,
            code,
            "LNURL-auth proves domain-specific Lightning key control, not treasury ownership.",
            R.PERFORM_LNURL_STEP_UP,
            now,
            evidence_fingerprint=str(evidence.get("lnurl_evidence_fingerprint") or "") or None,
            hard_cap=cap,
        )
    ]
