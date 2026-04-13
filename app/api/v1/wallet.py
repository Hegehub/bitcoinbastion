from fastapi import APIRouter

from app.schemas.base import ResponseEnvelope
from app.schemas.wallet import WalletHealthRequest, WalletHealthResponse
from app.services.wallet.health_service import WalletHealthService

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.post("/health", response_model=ResponseEnvelope[WalletHealthResponse])
def wallet_health(payload: WalletHealthRequest) -> ResponseEnvelope[WalletHealthResponse]:
    result = WalletHealthService().evaluate(payload)
    return ResponseEnvelope(data=result)
