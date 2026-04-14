from datetime import datetime

from pydantic import BaseModel, Field


class JobRunOut(BaseModel):
    id: int
    task_name: str
    status: str
    correlation_id: str
    started_at: datetime
    finished_at: datetime | None
    error_message: str

    model_config = {"from_attributes": True}


class JobRetryRequest(BaseModel):
    task_name: str = Field(min_length=3)


class JobRetryResponse(BaseModel):
    task_name: str
    task_id: str
