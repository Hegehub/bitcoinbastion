from fastapi import APIRouter

router = APIRouter(prefix="/treasury", tags=["treasury"])


@router.get("/requests")
def list_requests() -> dict[str, list[dict[str, str]]]:
    return {"items": []}
