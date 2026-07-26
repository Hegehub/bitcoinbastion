"""Wallet proof signals; this module never receives wallet secret material."""

from __future__ import annotations

from datetime import datetime

from app.domain.access.integrity import AccessIntegrityRecommendation as R
from app.domain.access.integrity import AccessIntegritySignal as Signal
from app.domain.access.integrity import AccessIntegritySignalCategory as C
from app.domain.access.integrity import AccessIntegritySignalStatus as S


def collect_wallet_signals(
    evidence: dict[str, object], now: datetime, maximum_points: int = 15
) -> list[Signal]:
    method = str(evidence.get("wallet_proof_method", "missing"))
    status, points, code, remedy, cap = (
        S.UNAVAILABLE,
        0.0,
        "wallet_proof_unavailable",
        R.REFRESH_WALLET_PROOF,
        None,
    )
    if evidence.get("wallet_proof_revoked"):
        status, code, cap = S.UNSAFE, "wallet_proof_revoked", 20
    elif evidence.get("wallet_network_mismatch"):
        status, code, cap = S.UNSAFE, "wallet_network_mismatch", 29
    elif method == "legacy_bitcoin_message":
        status, points, code, remedy = (
            S.DEGRADED,
            maximum_points * 0.35,
            "legacy_signature_compatibility",
            R.REPLACE_LEGACY_SIGNATURE,
        )
    elif method in {"bip322", "hardware_wallet", "air_gapped_wallet", "multi_wallet_quorum"}:
        raw_age = evidence.get("wallet_proof_age_seconds")
        age = raw_age if isinstance(raw_age, int) and not isinstance(raw_age, bool) else 10**9
        if age <= 86400:
            status, points, code = S.HEALTHY, float(maximum_points), "wallet_proof_recent"
        elif age <= 604800:
            status, points, code = S.ACCEPTABLE, maximum_points * 0.7, "wallet_proof_acceptable"
        else:
            status, points, code = S.DEGRADED, maximum_points * 0.25, "wallet_proof_stale"
        # Client-provided hardware class does not add points without verified evidence.
        if method == "hardware_wallet" and not evidence.get("hardware_evidence_verified"):
            status, points, code = (
                S.ACCEPTABLE,
                min(points, maximum_points * 0.7),
                "hardware_metadata_unverified",
            )
    return [
        Signal(
            "wallet-proof",
            C.WALLET_PROOF,
            status,
            points,
            maximum_points,
            code,
            "Wallet proof posture evaluated from verified metadata.",
            remedy,
            now,
            hard_cap=cap,
        )
    ]
