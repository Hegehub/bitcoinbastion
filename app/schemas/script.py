from pydantic import BaseModel, Field


class ScriptAnalysisOut(BaseModel):
    script_type: str
    complexity_score: float = Field(ge=0.0, le=1.0)
    risk_level: str
    confidence: float = Field(ge=0.0, le=1.0)
    freshness: dict[str, object]
    explainability: dict[str, object]


class DescriptorAwarenessOut(BaseModel):
    has_descriptor: bool
    has_recovery_instructions: bool
    has_backup_reference: bool
    completeness_score: float = Field(ge=0.0, le=1.0)
    recoverability_assumption: str
    warnings: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    freshness: dict[str, object]
    explainability: dict[str, object]
