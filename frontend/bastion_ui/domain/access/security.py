from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from bastion_ui.domain.provenance import Provenance
from bastion_ui.transport.generated_http import GetMeApiV1AccessMeGetSuccess


class SessionPosture(StrEnum):
    UNKNOWN = "UNKNOWN"
    ABSENT = "ABSENT"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    UNAVAILABLE = "UNAVAILABLE"


class EntitlementPosture(StrEnum):
    UNKNOWN = "UNKNOWN"
    NONE = "NONE"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    RESTRICTED = "RESTRICTED"
    UNAVAILABLE = "UNAVAILABLE"


class ProofOfPossessionPosture(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED_NOT_SATISFIED = "REQUIRED_NOT_SATISFIED"
    SATISFIED = "SATISFIED"
    UNKNOWN = "UNKNOWN"


class OperationProofPosture(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"
    SATISFIED_FOR_CURRENT_OPERATION = "SATISFIED_FOR_CURRENT_OPERATION"
    UNKNOWN = "UNKNOWN"


class SecurityPostureViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    session: SessionPosture
    entitlement: EntitlementPosture
    capabilities: tuple[str, ...]
    pop: ProofOfPossessionPosture
    human_intent: OperationProofPosture
    step_up: OperationProofPosture
    session_expires_at: datetime | None
    device_status: str | None
    provenance: Provenance
    limitation: str | None = None

    def browser_dump(self) -> dict[str, object]:
        return {
            "session": self.session.value,
            "entitlement": self.entitlement.value,
            "capabilities": list(self.capabilities),
            "pop": self.pop.value,
            "human_intent": self.human_intent.value,
            "step_up": self.step_up.value,
            "session_expires_at": self.session_expires_at.isoformat()
            if self.session_expires_at
            else None,
            "device_status": self.device_status,
            "provenance": self.provenance.browser_dump(),
            "limitation": self.limitation,
        }


def adapt_access_me(
    response: GetMeApiV1AccessMeGetSuccess, provenance: Provenance
) -> SecurityPostureViewModel:
    payload = response.root
    session = SessionPosture.ACTIVE
    if payload.device_status.lower() == "revoked":
        session = SessionPosture.REVOKED
    entitlement = {
        "active": EntitlementPosture.ACTIVE,
        "expired": EntitlementPosture.EXPIRED,
        "restricted": EntitlementPosture.RESTRICTED,
    }.get(payload.entitlement_status.lower(), EntitlementPosture.UNKNOWN)
    return SecurityPostureViewModel(
        session=session,
        entitlement=entitlement,
        capabilities=tuple(sorted(payload.active_scopes)),
        pop=ProofOfPossessionPosture.UNKNOWN,
        human_intent=OperationProofPosture.NOT_REQUIRED,
        step_up=OperationProofPosture.UNKNOWN,
        session_expires_at=payload.session_expires_at,
        device_status=payload.device_status,
        provenance=provenance,
        limitation="Frontend posture is advisory; the backend decision always wins.",
    )
