from __future__ import annotations

import time
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.repositories.delivery_repository import DeliveryRepository
from app.integrations.bitcoin.provider import BitcoinProviderError, build_bitcoin_provider
from app.schemas.observability import ProviderHealthEvidenceOut


class ProviderHealthService:
    def collect(self, db: Session) -> list[ProviderHealthEvidenceOut]:
        items: list[ProviderHealthEvidenceOut] = [self._collect_onchain_health(db=db)]
        items.append(self._collect_rss_health())
        items.append(self._collect_delivery_health(db=db))
        return items

    def _collect_onchain_health(self, db: Session) -> ProviderHealthEvidenceOut:
        settings = get_settings()
        provider = build_bitcoin_provider(settings)
        start = time.perf_counter()
        now = datetime.now(UTC)
        try:
            events = provider.recent_events()
            latency_ms = int((time.perf_counter() - start) * 1000)
            payload = dict(events[0].payload) if events else {}
            source_type = str(payload.get("source_type", "provider"))
            is_fallback = bool(payload.get("is_fallback", False))
            is_mock = bool(payload.get("is_mock", False))
            confidence = 0.95
            if is_fallback:
                confidence -= 0.25
            if is_mock:
                confidence -= 0.3
            return ProviderHealthEvidenceOut(
                provider_name=str(payload.get("provider_name", getattr(provider, "__class__", type(provider)).__name__)),
                provider_type="bitcoin",
                checked_at=now,
                healthy=len(events) > 0,
                latency_ms=max(0, latency_ms),
                source_type=source_type,
                is_fallback=is_fallback,
                is_mock=is_mock,
                confidence=max(0.1, min(1.0, confidence)),
                freshness_seconds=0,
                limitations=[str(payload.get("limitations", ""))] if payload.get("limitations") else [],
                evidence_refs=[f"onchain_events:{len(events)}", f"provider:{payload.get('provider_name', 'unknown')}"]
            )
        except Exception as exc:  # noqa: BLE001
            latency_ms = int((time.perf_counter() - start) * 1000)
            return ProviderHealthEvidenceOut(
                provider_name="onchain_unavailable",
                provider_type="bitcoin",
                checked_at=now,
                healthy=False,
                latency_ms=max(0, latency_ms),
                error_type=type(exc).__name__,
                error_message=self._sanitize_error(str(exc)),
                source_type="fallback",
                is_fallback=True,
                is_mock=isinstance(exc, BitcoinProviderError),
                confidence=0.2,
                freshness_seconds=0,
                limitations=["Provider probe failed; runtime in fallback/no-provider mode."],
                evidence_refs=["provider_probe:onchain", "state:fallback"],
            )

    def _collect_rss_health(self) -> ProviderHealthEvidenceOut:
        now = datetime.now(UTC)
        freshness_seconds = 3600
        return ProviderHealthEvidenceOut(
            provider_name="rss_passive",
            provider_type="rss",
            checked_at=now,
            healthy=True,
            latency_ms=0,
            source_type="passive",
            confidence=0.6,
            freshness_seconds=freshness_seconds,
            limitations=["RSS provider health not actively probed in this pipeline; passive status only."],
            evidence_refs=["rss:passive_health"],
        )

    def _collect_delivery_health(self, db: Session) -> ProviderHealthEvidenceOut:
        failed = DeliveryRepository(db).failed_count_last_24h()
        healthy = failed == 0
        return ProviderHealthEvidenceOut(
            provider_name="telegram",
            provider_type="delivery",
            checked_at=datetime.now(UTC),
            healthy=healthy,
            latency_ms=0,
            source_type="delivery_logs",
            confidence=0.85 if healthy else 0.55,
            freshness_seconds=300,
            limitations=["Delivery health is inferred from persisted logs, not active Telegram probe."],
            evidence_refs=[f"delivery_failures_24h:{failed}"],
            error_type="DeliveryFailures" if not healthy else None,
            error_message="Delivery failures in past 24h" if not healthy else None,
        )

    @staticmethod
    def _sanitize_error(message: str) -> str:
        cleaned = " ".join(message.split())
        cleaned = cleaned.replace("\n", " ")
        return cleaned[:180]
