from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.news_source import NewsSource
from app.services.market_intelligence.validation.urls import validate_http_url

yaml_any: Any = yaml


class SourceCategory(StrEnum):
    BITCOIN_CORE = "bitcoin_core"
    BITCOIN_MEDIA = "bitcoin_media"
    MARKET_MEDIA = "market_media"
    MACRO = "macro"
    REGULATORY = "regulatory"
    SECURITY = "security"
    MINING = "mining"
    LIGHTNING = "lightning"
    INSTITUTIONAL = "institutional"
    EXCHANGE = "exchange"
    ONCHAIN = "onchain"
    RESEARCH = "research"
    GOVERNMENT = "government"
    ETF = "etf"
    SOVEREIGNTY = "sovereignty"
    DEVELOPER = "developer"
    GENERAL_CRYPTO = "general_crypto"


class SourceTier(StrEnum):
    SOVEREIGN = "sovereign"
    BITCOIN_NATIVE = "bitcoin_native"
    INSTITUTIONAL = "institutional"
    OFFICIAL = "official"
    RESEARCH = "research"
    MARKET_MEDIA = "market_media"
    GENERAL_CRYPTO = "general_crypto"
    COMMUNITY = "community"
    EXPERIMENTAL = "experimental"


class SourceKind(StrEnum):
    RSS = "rss"
    ATOM = "atom"
    JSON_FEED = "json_feed"
    HTML_SCRAPE = "html_scrape"
    API = "api"
    MANUAL = "manual"
    INTERNAL = "internal"


@dataclass
class SourceSeedResult:
    created: int
    updated: int


class SourceRegistryService:
    def list_sources(self, db: Session) -> list[NewsSource]:
        return list(db.execute(select(NewsSource).order_by(NewsSource.name.asc())).scalars())

    def get_source(self, db: Session, source_id: int) -> NewsSource | None:
        return db.get(NewsSource, source_id)

    def create_source(self, db: Session, payload: dict[str, object]) -> NewsSource:
        self._validate_payload(payload)
        source = NewsSource(**payload)
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    def update_source(self, db: Session, source_id: int, payload: dict[str, object]) -> NewsSource:
        source = self.get_source(db, source_id)
        if source is None:
            raise ValueError("source not found")
        self._validate_payload(payload, partial=True)
        for key, value in payload.items():
            setattr(source, key, value)
        db.commit()
        db.refresh(source)
        return source

    def disable_source(self, db: Session, source_id: int) -> None:
        self.update_source(db, source_id, {"is_active": False})

    def enable_source(self, db: Session, source_id: int) -> None:
        self.update_source(db, source_id, {"is_active": True})

    def sync_from_yaml(
        self, db: Session, yaml_path: Path, *, override_activity: bool = False
    ) -> SourceSeedResult:
        rows = yaml_any.safe_load(yaml_path.read_text()) or []
        created = 0
        updated = 0
        for row in rows:
            payload = self._yaml_to_payload(row)
            existing = db.execute(
                select(NewsSource).where(NewsSource.slug == payload["slug"])
            ).scalar_one_or_none()
            if existing is None:
                self.create_source(db, payload)
                created += 1
                continue
            if not override_activity:
                payload.pop("is_active", None)
            for k, v in payload.items():
                setattr(existing, k, v)
            updated += 1
        db.commit()
        return SourceSeedResult(created=created, updated=updated)

    def calculate_source_baseline_confidence(
        self, tier: SourceTier, category: SourceCategory
    ) -> float:
        base = 0.55
        if tier in {SourceTier.SOVEREIGN, SourceTier.OFFICIAL, SourceTier.INSTITUTIONAL}:
            base += 0.25
        if tier == SourceTier.EXPERIMENTAL:
            base -= 0.2
        if category in {SourceCategory.BITCOIN_CORE, SourceCategory.REGULATORY, SourceCategory.ETF}:
            base += 0.1
        return max(0.1, min(0.99, round(base, 2)))

    def _validate_payload(self, payload: dict[str, object], partial: bool = False) -> None:
        for url_field in ("base_url", "rss_url", "homepage_url"):
            value = payload.get(url_field)
            if value:
                validate_http_url(str(value))
        for score_field in (
            "credibility_weight",
            "signal_quality_weight",
            "sovereignty_weight",
            "default_confidence",
        ):
            value = payload.get(score_field)
            if value is not None and not (0.0 <= float(str(value)) <= 1.0):
                raise ValueError(f"invalid {score_field}")
        if "fetch_interval_minutes" in payload and int(str(payload["fetch_interval_minutes"])) <= 0:
            raise ValueError("fetch_interval_minutes must be > 0")
        if "category" in payload:
            SourceCategory(str(payload["category"]))
        if "tier" in payload:
            SourceTier(str(payload["tier"]))
        if "kind" in payload:
            SourceKind(str(payload["kind"]))

    def _yaml_to_payload(self, row: dict[str, object]) -> dict[str, object]:
        tier = SourceTier(str(row["tier"]))
        category = SourceCategory(str(row["category"]))
        return {
            "name": row["name"],
            "slug": row["slug"],
            "kind": str(row["kind"]),
            "base_url": row.get("base_url", ""),
            "rss_url": row.get("rss_url", ""),
            "homepage_url": row.get("homepage_url", ""),
            "language": row.get("language", "en"),
            "country_code": row.get("country_code"),
            "category": str(category),
            "tier": str(tier),
            "credibility_weight": float(str(row.get("credibility_weight", 0.7))),
            "signal_quality_weight": float(str(row.get("signal_quality_weight", 0.7))),
            "sovereignty_weight": float(str(row.get("sovereignty_weight", 0.7))),
            "default_confidence": float(
                str(
                    row.get(
                        "default_confidence",
                        self.calculate_source_baseline_confidence(tier, category),
                    )
                )
            ),
            "is_active": bool(row.get("is_active", True)),
            "is_public": bool(row.get("is_public", True)),
            "fetch_interval_minutes": int(str(row.get("fetch_interval_minutes", 15))),
            "request_timeout_seconds": int(str(row.get("request_timeout_seconds", 15))),
            "tags_json": row.get("tags", []),
        }
