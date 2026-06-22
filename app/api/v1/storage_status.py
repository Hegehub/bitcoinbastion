"""Operational Storage Layer status endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.core.cache import get_redis_client
from app.core.config import get_settings
from app.storage.health_checks import collect_storage_status
from app.storage.schemas import StorageStatusResponse

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get(
    "/status",
    response_model=StorageStatusResponse,
    summary="Storage status for Bitcoin Bastion storage engines.",
)
async def storage_status(db: Session = Depends(db_session)) -> StorageStatusResponse:
    """Return sanitized operational status for configured storage engines."""

    return await collect_storage_status(
        settings=get_settings(),
        db=db,
        redis_client_factory=get_redis_client,
    )
