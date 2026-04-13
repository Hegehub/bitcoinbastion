from datetime import datetime

from pydantic import BaseModel, Field


class TreasuryRequestIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    amount_sats: int = Field(gt=0)
    destination_reference: str = Field(min_length=5, max_length=255)


class TreasuryRequestOut(BaseModel):
    id: int
    title: str
    amount_sats: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
