from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.core.config import get_settings
from app.core.telemetry import increment_onchain_provider_probe_event
from app.db.repositories.onchain_repository import OnchainRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.onchain import OnchainChainStateOut, OnchainEventOut
from app.integrations.bitcoin.provider import BitcoinProviderError, build_bitcoin_provider
from app.services.blockchain.chain_state_service import ChainStateService

router = APIRouter(prefix="/onchain", tags=["onchain"])


@router.get("/events", response_model=ResponseEnvelope[PaginatedData[OnchainEventOut]])
def onchain_events(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[OnchainEventOut]]:
    repo = OnchainRepository(db)
    items = [OnchainEventOut.model_validate(item) for item in repo.recent(limit=limit, offset=offset)]
    return ResponseEnvelope(data=PaginatedData(items=items, total=repo.count(), limit=limit, offset=offset))


@router.get("/state", response_model=ResponseEnvelope[OnchainChainStateOut])
def onchain_state(
    tip_height: int | None = None,
    observed_block_height: int | None = None,
    headers_height: int | None = None,
    provider_probe: bool = False,
    db: Session = Depends(db_session),
) -> ResponseEnvelope[OnchainChainStateOut]:
    repo = OnchainRepository(db)
    observed = observed_block_height
    source = "query" if observed_block_height is not None else "repository_fallback"
    if observed is None:
        observed = repo.latest_block_height()
    if observed is None:
        observed = 899_995

    tip = tip_height if tip_height is not None else observed + 1
    provider_tip: int | None = None
    provider_confidence: float | None = None
    provider_data_age_seconds: int | None = None
    if tip_height is None and provider_probe:
        try:
            provider = build_bitcoin_provider(get_settings())
            events = provider.recent_events()
            if events:
                provider_tip = max(item.block_height for item in events)
                tip = max(tip, provider_tip)
                provider_confidence = 0.82
                provider_data_age_seconds = 15
                source = "provider_probe"
                increment_onchain_provider_probe_event(outcome="success")
            else:
                provider_confidence = 0.55
                provider_data_age_seconds = 180
                increment_onchain_provider_probe_event(outcome="empty")
        except BitcoinProviderError:
            provider_confidence = 0.42
            provider_data_age_seconds = 900
            increment_onchain_provider_probe_event(outcome="fallback")
            pass
    headers = headers_height if headers_height is not None else tip

    state = ChainStateService().evaluate(
        tip_height=tip,
        observed_block_height=observed,
        headers_height=headers,
        provider_tip_height=provider_tip,
        provider_confidence=provider_confidence,
        provider_data_age_seconds=provider_data_age_seconds,
        data_source=source,
    )
    state.explainability["data_source"] = source
    state.explainability["provider_confidence"] = provider_confidence
    state.explainability["provider_data_age_seconds"] = provider_data_age_seconds
    return ResponseEnvelope(data=OnchainChainStateOut.model_validate(state, from_attributes=True))
