from datetime import datetime

from pydantic import BaseModel


class JobRunOut(BaseModel):
    id: int
    task_name: str
    status: str
    correlation_id: str
    started_at: datetime
    finished_at: datetime | None
    error_message: str

    model_config = {"from_attributes": True}
