from pydantic import BaseModel, ConfigDict, Field


class PageParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ExplainabilityOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    explanation: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    data_sources: list[str] = Field(default_factory=list)


class FreshnessOut(BaseModel):
    computed_at: str | None = None
    ttl_seconds: int | None = Field(default=None, ge=0)
    is_stale: bool = False
    stale_reason: str = ""
