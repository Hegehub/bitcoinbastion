from pathlib import Path

from app.db.session import SessionLocal
from app.services.market_intelligence.source_registry import SourceRegistryService


def main() -> None:
    path = Path("config/news_sources/default_sources.yaml")
    with SessionLocal() as db:
        result = SourceRegistryService().sync_from_yaml(db, path)
        print(f"seeded created={result.created} updated={result.updated}")


if __name__ == "__main__":
    main()
