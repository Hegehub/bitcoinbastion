from dataclasses import dataclass

from app.db.models.signal import Signal
from app.db.models.onchain import OnchainEvent
from app.db.repositories.onchain_repository import OnchainRepository
from app.integrations.bitcoin.provider import BitcoinProvider
from app.services.alerts.signal_engine import SignalEngine
from app.services.events.domain_event_publisher import publish_domain_event
from app.services.scoring.onchain_scoring import OnchainScoringService
from app.services.bitcoin_observations.producer import BitcoinObservationProducer


@dataclass
class GeneratedOnchainSignal:
    signal: Signal
    source_type: str
    source_id: str
    event: OnchainEvent


class OnchainIngestionService:
    def __init__(self, provider: BitcoinProvider, onchain_repo: OnchainRepository) -> None:
        self.provider = provider
        self.onchain_repo = onchain_repo
        self.scoring = OnchainScoringService()

    def ingest_and_generate_signals(self) -> list[GeneratedOnchainSignal]:
        events = self.provider.recent_events()
        engine = SignalEngine()
        signals: list[GeneratedOnchainSignal] = []

        for event in events:
            score = self.scoring.score(event)
            observation_batch = BitcoinObservationProducer(self.onchain_repo).persist_chain_event(
                event,
                significance=score.significance,
                confidence=score.confidence,
                explainability=self._normalize_explainability(score.explainability),
                tags=score.tags,
            )
            if not observation_batch.observations:
                continue
            model_event = observation_batch.persisted_event
            if model_event is None:
                continue
            self._publish_onchain_event(model_event)
            signal = engine.from_onchain_event(model_event)
            signals.append(
                GeneratedOnchainSignal(
                    signal=signal,
                    source_type="onchain_event",
                    source_id=SignalEngine.onchain_source_id(model_event),
                    event=model_event,
                )
            )

        return signals

    def _publish_onchain_event(self, event: OnchainEvent) -> None:
        event_type = {
            "large_transfer": "onchain.large_transfer",
            "watchlist_hit": "onchain.watchlist_hit",
            "fee_spike": "onchain.fee_spike",
            "mempool_pressure": "onchain.mempool_pressure",
        }.get(event.event_type)
        if event_type is None:
            return
        publish_domain_event(
            self.onchain_repo.db,
            event_type,
            {
                "event_id": event.id,
                "chain": "bitcoin",
                "address_or_tx_ref": event.txid or event.address,
                "amount_sats": event.value_sats,
                "fee_rate": event.fee_sats,
                "block_height": event.block_height,
                "provider_confidence": event.confidence_score,
                "data_source": event.provider,
                "limitations": ["On-chain events use public chain/provider data only."],
                "public_data_only": True,
                "no_custody": True,
            },
            aggregate_type="onchain_event",
            aggregate_id=event.id,
            source="onchain_ingestion",
            idempotency_key=f"{event_type}:onchain_event:{event.id}:created",
        )

    @staticmethod
    def _normalize_explainability(payload: dict[str, object]) -> dict[str, float | str]:
        normalized: dict[str, float | str] = {}
        for key, value in payload.items():
            if isinstance(value, (str, float)):
                normalized[key] = value
            elif isinstance(value, int) and not isinstance(value, bool):
                normalized[key] = float(value)
        return normalized
