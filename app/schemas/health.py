from pydantic import BaseModel, Field


class HealthOut(BaseModel):
    status: str
    app: str
    details: dict[str, str] = Field(default_factory=dict)
