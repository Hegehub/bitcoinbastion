from dataclasses import dataclass

from app.db.models.signal import Signal
from app.db.models.onchain import OnchainEvent
from app.db.repositories.onchain_repository import OnchainRepository
from app.integrations.bitcoin.provider import BitcoinProvider
from app.services.alerts.signal_engine import SignalEngine
from app.services.scoring.onchain_scoring import OnchainScoringService


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
            model_event = self.onchain_repo.add_event(
                event,
                significance=score.significance,
                confidence=score.confidence,
                explainability=score.explainability,
                tags=score.tags,
            )
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
