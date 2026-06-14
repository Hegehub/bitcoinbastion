import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.event_outbox import EventOutbox
from app.db.models.wallet import WalletProfile
from app.db.repositories.onchain_repository import OnchainRepository
from app.db.repositories.wallet_repository import WalletRepository
from app.integrations.bitcoin.provider import MockBitcoinProvider
from app.schemas.wallet import WalletHealthResponse
from app.services.ingestion.onchain_ingestion import OnchainIngestionService
from app.services.market_data.provider_health import record_provider_result


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_provider_health_degradation_and_recovery_emit_outbox_events() -> None:
    with _session() as db:
        for _ in range(3):
            record_provider_result(
                db, "market_provider", success=False, latency_ms=900, error="timeout"
            )
        record_provider_result(db, "market_provider", success=True, latency_ms=100)
        record_provider_result(db, "market_provider", success=True, latency_ms=100)
        record_provider_result(db, "market_provider", success=True, latency_ms=100)
        db.commit()

        event_types = [
            row.event_type for row in db.query(EventOutbox).order_by(EventOutbox.id).all()
        ]
        assert "provider.degraded" in event_types
        assert "provider.recovered" in event_types
        degraded = db.query(EventOutbox).filter_by(event_type="provider.degraded").one()
        payload = json.loads(degraded.payload_json)
        assert payload["degraded"] is True
        assert payload["fallback_active"] is True


def test_onchain_ingestion_emits_large_transfer_event() -> None:
    with _session() as db:
        generated = OnchainIngestionService(
            MockBitcoinProvider(), OnchainRepository(db)
        ).ingest_and_generate_signals()

        event = db.query(EventOutbox).filter_by(event_type="onchain.large_transfer").one()
        payload = json.loads(event.payload_json)
        assert generated
        assert payload["chain"] == "bitcoin"
        assert payload["public_data_only"] is True
        assert payload["no_custody"] is True


def test_wallet_health_generation_emits_no_custody_events() -> None:
    with _session() as db:
        profile = WalletProfile(
            user_id=1,
            name="watch-only treasury",
            descriptor_or_reference="watch-only-reference",
            watch_only=True,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

        WalletRepository(db).create_health_report(
            profile.id,
            WalletHealthResponse(
                health_score=60,
                utxo_fragmentation_score=70,
                privacy_score=0.2,
                fee_exposure_score=40,
                recommendations=["Review address reuse exposure."],
                confidence=0.7,
            ),
        )

        event_types = {row.event_type for row in db.query(EventOutbox).all()}
        assert "wallet.health.generated" in event_types
        assert "wallet.privacy_risk.high" in event_types
        payload = json.loads(
            db.query(EventOutbox).filter_by(event_type="wallet.health.generated").one().payload_json
        )
        assert payload["no_custody"] is True
        assert "seed phrase" not in json.dumps(payload).casefold()
        assert "private key" not in json.dumps(payload).casefold()


def test_unwired_event_gaps_are_documented() -> None:
    gap_doc = Path("docs/EVENT_INTEGRATION_GAPS.md").read_text()
    assert "news.article.scored" in gap_doc
    assert "trace.risk_band.changed" in gap_doc
    assert "provider.stale" in gap_doc
    assert "taxonomy expansion" in gap_doc.casefold()
