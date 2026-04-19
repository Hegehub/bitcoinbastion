from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import db_session, get_current_user
from app.db.models.auth import User
from app.db.repositories.wallet_repository import WalletRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.wallet import (
    WalletHealthReportOut,
    WalletHealthRequest,
    WalletHealthResponse,
    WalletProfileOut,
)
from app.services.wallet.health_service import WalletHealthService

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.post("/health", response_model=ResponseEnvelope[WalletHealthResponse])
def wallet_health(payload: WalletHealthRequest) -> ResponseEnvelope[WalletHealthResponse]:
    result = WalletHealthService().evaluate(payload)
    return ResponseEnvelope(data=result)


@router.post("/profiles/{wallet_profile_id}/health", response_model=ResponseEnvelope[WalletHealthReportOut])
def generate_wallet_profile_health_report(
    wallet_profile_id: int,
    payload: WalletHealthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[WalletHealthReportOut]:
    repo = WalletRepository(db)
    profile = repo.get_profile(wallet_profile_id)
    if profile is None or profile.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Wallet profile not found")

    service = WalletHealthService()
    health = service.evaluate(payload)
    report = repo.create_health_report(wallet_profile_id=wallet_profile_id, health=health)
    return ResponseEnvelope(data=service.to_report_out(report))


@router.get("/profiles/{wallet_profile_id}/health/reports", response_model=ResponseEnvelope[PaginatedData[WalletHealthReportOut]])
def list_wallet_profile_health_reports(
    wallet_profile_id: int,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[WalletHealthReportOut]]:
    repo = WalletRepository(db)
    profile = repo.get_profile(wallet_profile_id)
    if profile is None or profile.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Wallet profile not found")

    service = WalletHealthService()
    reports = [service.to_report_out(item) for item in repo.list_health_reports(wallet_profile_id, limit, offset)]
    total = repo.count_health_reports(wallet_profile_id)
    return ResponseEnvelope(data=PaginatedData(items=reports, total=total, limit=limit, offset=offset))


@router.get("/profiles", response_model=ResponseEnvelope[PaginatedData[WalletProfileOut]])
def list_profiles(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[PaginatedData[WalletProfileOut]]:
    repo = WalletRepository(db)
    items = [
        WalletProfileOut.model_validate(item)
        for item in repo.list_by_user(user_id=current_user.id, limit=limit, offset=offset)
    ]
    total = repo.count_by_user(current_user.id)
    return ResponseEnvelope(data=PaginatedData(items=items, total=total, limit=limit, offset=offset))
