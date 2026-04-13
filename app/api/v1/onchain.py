from fastapi import APIRouter

router = APIRouter(prefix="/onchain", tags=["onchain"])


@router.get("/events")
def onchain_events() -> dict[str, list[dict[str, str]]]:
    return {"items": []}
