from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EntitlementView:
    plan: str
    status: str
    scopes: tuple[str, ...]
    metric_groups: tuple[str, ...]
    crypto_epoch: int | None = None
    access_certificate_required: bool = False
    pq_verification_status: str = "unsupported"

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> "EntitlementView":
        scopes = payload.get("scopes")
        metrics = payload.get("metric_groups")
        crypto_epoch = payload.get("crypto_epoch")
        return cls(
            plan=str(payload.get("plan", "")),
            status=str(payload.get("status", "")),
            scopes=tuple(v for v in scopes if isinstance(v, str))
            if isinstance(scopes, list)
            else (),
            metric_groups=tuple(v for v in metrics if isinstance(v, str))
            if isinstance(metrics, list)
            else (),
            crypto_epoch=int(crypto_epoch)
            if isinstance(crypto_epoch, (str, int)) and crypto_epoch
            else None,
            access_certificate_required=bool(payload.get("access_certificate_required", False)),
            pq_verification_status=str(payload.get("pq_verification_status", "unsupported")),
        )
