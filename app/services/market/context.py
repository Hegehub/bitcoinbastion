from sqlalchemy.orm import Session

from app.services.market.collector import BTCPriceCollector


class BTCMarketContextService:
    def get_current_context(self, db: Session) -> dict[str, object]:
        return BTCPriceCollector().collect(db).__dict__
