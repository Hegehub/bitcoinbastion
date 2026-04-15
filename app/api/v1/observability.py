from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.schemas.base import ResponseEnvelope
from app.schemas.observability import OperationsSnapshotOut
from app.services.observability.operations_service import OperationsSnapshotService

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/snapshot", response_model=ResponseEnvelope[OperationsSnapshotOut])
def operations_snapshot(db: Session = Depends(db_session)) -> ResponseEnvelope[OperationsSnapshotOut]:
    return ResponseEnvelope(data=OperationsSnapshotService().snapshot(db=db))
