from sqlalchemy.orm import Session

from app.db.models.treasury import TreasuryRequest
from app.schemas.treasury import TreasuryRequestIn


class TreasuryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_request(self, payload: TreasuryRequestIn, requested_by: int | None = None) -> TreasuryRequest:
        request = TreasuryRequest(
            title=payload.title,
            amount_sats=payload.amount_sats,
            destination_reference=payload.destination_reference,
            requested_by=requested_by,
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request
