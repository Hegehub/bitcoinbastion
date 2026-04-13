from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/status")
def admin_status() -> dict[str, str]:
    return {"status": "ok", "module": "admin"}
