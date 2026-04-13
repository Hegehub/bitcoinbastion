from fastapi import APIRouter

router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("")
def list_entities() -> dict[str, list[dict[str, str]]]:
    return {"items": []}
