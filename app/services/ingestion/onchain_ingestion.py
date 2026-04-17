from app.db.models.signal import Signal
from app.db.repositories.onchain_repository import OnchainRepository
from app.integrations.bitcoin.provider import BitcoinProvider
from app.services.alerts.signal_engine import SignalEngine
from app.services.scoring.onchain_scoring import OnchainScoringService


class OnchainIngestionService:
    def __init__(self, provider: BitcoinProvider, onchain_repo: OnchainRepository) -> None:
        self.provider = provider
        self.onchain_repo = onchain_repo
        self.scoring = OnchainScoringService()

    def ingest_and_generate_signals(self) -> list[Signal]:
        events = self.provider.recent_events()
        engine = SignalEngine()
        signals: list[Signal] = []

        for event in events:
            score = self.scoring.score(event)
            model_event = self.onchain_repo.add_event(
                event,
                significance=score.significance,
                confidence=score.confidence,
                explainability=score.explainability,
                tags=score.tags,
            )
            signals.append(engine.from_onchain_event(model_event))

        return signals
