from fastapi import APIRouter

from app.schemas.base import ResponseEnvelope
from app.schemas.observability import OperationsSnapshotOut
from app.services.observability.operations_service import OperationsSnapshotService

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/snapshot", response_model=ResponseEnvelope[OperationsSnapshotOut])
def operations_snapshot() -> ResponseEnvelope[OperationsSnapshotOut]:
    return ResponseEnvelope(data=OperationsSnapshotService().snapshot())
