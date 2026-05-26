from pydantic import BaseModel


class SourceHealthResponse(BaseModel):
    source_id: int
    status: str
    health_score: float
