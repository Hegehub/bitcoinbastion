from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StepUpRequirement:
    action: str
    required_auth: tuple[str, ...]
    scopes: tuple[str, ...] = ()
    risk: str = "high"
    human_intent: str | None = None
    quorum_requirement: str | None = None
