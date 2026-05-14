from pydantic import BaseModel, ConfigDict, Field


class PageParams(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ExplainabilityOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    explanation: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    data_sources: list[str] = Field(default_factory=list)

class ExplainabilityContractOut(BaseModel):
    """Unified machine-readable explainability contract (additive)."""

    model_config = ConfigDict(extra="allow")

    version: str = "exp_v1"
    domain: str = "unknown"
    source_type: str = "unknown"
    provider_name: str = "unknown"
    is_mock: bool = False
    is_fallback: bool = False
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    freshness: dict[str, object] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    signals: dict[str, object] = Field(default_factory=dict)


class FreshnessOut(BaseModel):
    computed_at: str | None = None
    ttl_seconds: int | None = Field(default=None, ge=0)
    is_stale: bool = False
    stale_reason: str = ""
