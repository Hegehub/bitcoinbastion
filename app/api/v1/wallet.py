from fastapi import APIRouter

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/health")
def wallet_health() -> dict[str, str]:
    return {"status": "not-configured"}
