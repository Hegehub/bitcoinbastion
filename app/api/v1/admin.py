from fastapi import APIRouter, Depends

from app.api.dependencies import get_admin_user
from app.db.models.auth import User
from app.schemas.base import ResponseEnvelope

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/status", response_model=ResponseEnvelope[dict[str, str]])
def admin_status(_: User = Depends(get_admin_user)) -> ResponseEnvelope[dict[str, str]]:
    return ResponseEnvelope(data={"status": "ok", "module": "admin"})
