from datetime import datetime

from pydantic import BaseModel


class SignalOut(BaseModel):
    id: int
    signal_type: str
    severity: str
    score: float
    confidence: float
    title: str
    summary: str
    is_published: bool
    created_at: datetime

    model_config = {"from_attributes": True}
