from dataclasses import dataclass


@dataclass(slots=True)
class ScriptProfile:
    script_type: str
    complexity_score: float
    risk_level: str
