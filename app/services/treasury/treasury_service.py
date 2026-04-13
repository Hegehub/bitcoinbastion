from app.db.models.treasury import TreasuryRequest
from app.db.repositories.treasury_repository import TreasuryRepository
from app.schemas.treasury import TreasuryRequestIn


class TreasuryService:
    def __init__(self, repo: TreasuryRepository) -> None:
        self.repo = repo

    def create_request(self, payload: TreasuryRequestIn, requested_by: int | None = None) -> TreasuryRequest:
        request = TreasuryRequest(
            title=payload.title,
            amount_sats=payload.amount_sats,
            destination_reference=payload.destination_reference,
            requested_by=requested_by,
        )
        return self.repo.create(request)

    def list_requests(self, limit: int, offset: int, status: str | None = None) -> list[TreasuryRequest]:
        return self.repo.list(limit=limit, offset=offset, status=status)

    def count_requests(self, status: str | None = None) -> int:
        return self.repo.count(status=status)
