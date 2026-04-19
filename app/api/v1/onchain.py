from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.repositories.onchain_repository import OnchainRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.onchain import OnchainChainStateOut, OnchainEventOut
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
    db: Session = Depends(db_session),
) -> ResponseEnvelope[OnchainChainStateOut]:
    repo = OnchainRepository(db)
    observed = observed_block_height
    if observed is None:
        observed = repo.latest_block_height()
    if observed is None:
        observed = 899_995

    tip = tip_height if tip_height is not None else observed + 1
    headers = headers_height if headers_height is not None else tip

    state = ChainStateService().evaluate(
        tip_height=tip,
        observed_block_height=observed,
        headers_height=headers,
    )
    state.explainability["data_source"] = "query" if observed_block_height is not None else "repository_fallback"
    return ResponseEnvelope(data=OnchainChainStateOut.model_validate(state, from_attributes=True))
