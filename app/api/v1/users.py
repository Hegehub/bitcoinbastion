from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.access_dependencies import require_access_session, require_plan
from app.api.dependencies import db_session
from app.domain.access.context import AccessContext
from app.domain.access.plans import PlanCode
from app.db.repositories.user_repository import UserRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.user import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=ResponseEnvelope[PaginatedData[UserOut]])
def list_users(
    limit: int = 20,
    offset: int = 0,
    _: AccessContext = Depends(require_plan(PlanCode.ENTERPRISE)),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[UserOut]]:
    repo = UserRepository(db)
    users = repo.list_users(limit=limit, offset=offset)
    total = repo.count()
    return ResponseEnvelope(
        data=PaginatedData(items=[UserOut.model_validate(user) for user in users], total=total, limit=limit, offset=offset)
    )


@router.get("/me", response_model=ResponseEnvelope[UserOut])
def me(access_context: AccessContext = Depends(require_access_session)) -> ResponseEnvelope[UserOut]:
    return ResponseEnvelope(
        data=UserOut(
            id=0,
            email="access-subject@bitcoinbastion.invalid",
            username=access_context.certificate_fingerprint,
            role=access_context.plan_code.value,
            is_active=True,
        )
    )
