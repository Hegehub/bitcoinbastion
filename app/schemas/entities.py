from datetime import datetime

from pydantic import BaseModel


class EntityOut(BaseModel):
    id: int
    name: str
    entity_type: str
    label: str
    description: str
    confidence: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WatchedEntityOut(BaseModel):
    id: int
    name: str
    entity_type: str
    label: str
    address: str
    watch_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
