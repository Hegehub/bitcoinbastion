from fastapi import APIRouter

from app.schemas.base import ResponseEnvelope
from app.schemas.policy import PolicyCheckRequest, PolicyCheckResponse
from app.services.policy.policy_service import TreasuryPolicyService

router = APIRouter(prefix="/policy", tags=["policy"])


@router.post("/check", response_model=ResponseEnvelope[PolicyCheckResponse])
def check_policy(payload: PolicyCheckRequest) -> ResponseEnvelope[PolicyCheckResponse]:
    result = TreasuryPolicyService().evaluate(payload)
    return ResponseEnvelope(data=result)
