from fastapi import APIRouter

router = APIRouter(prefix="/fees", tags=["fees"])


@router.get("/snapshot")
def fee_snapshot() -> dict[str, str]:
    return {"state": "unknown"}
