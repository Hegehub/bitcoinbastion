from datetime import datetime

from pydantic import BaseModel


class OnchainEventOut(BaseModel):
    id: int
    event_type: str
    txid: str
    address: str
    value_sats: int
    block_height: int
    observed_at: datetime
    significance_score: float
    confidence_score: float

    model_config = {"from_attributes": True}


class OnchainChainStateOut(BaseModel):
    tip_height: int
    observed_block_height: int
    headers_height: int
    confirmation_depth: int
    reorg_risk_score: float
    finality_score: float
    finality_band: str
    explainability: dict[str, object]
