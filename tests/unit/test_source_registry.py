from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.services.market_intelligence.source_registry import SourceCategory, SourceRegistryService, SourceTier


@pytest.fixture()
def db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as s:
        yield s


def test_baseline_confidence() -> None:
    svc = SourceRegistryService()
    assert svc.calculate_source_baseline_confidence(SourceTier.SOVEREIGN, SourceCategory.BITCOIN_CORE) > svc.calculate_source_baseline_confidence(SourceTier.EXPERIMENTAL, SourceCategory.GENERAL_CRYPTO)


def test_invalid_category_rejected(db: Session) -> None:
    svc = SourceRegistryService()
    with pytest.raises(ValueError):
        svc.create_source(db, {"name": "X", "slug": "x", "kind": "rss", "base_url": "https://x.com", "rss_url": "https://x.com/rss", "homepage_url": "https://x.com", "category": "bad", "tier": "sovereign", "fetch_interval_minutes": 10})


def test_yaml_sync(tmp_path: Path, db: Session) -> None:
    svc = SourceRegistryService()
    p = tmp_path / "s.yaml"
    p.write_text("- name: A\n  slug: a\n  kind: rss\n  base_url: https://a.com\n  rss_url: https://a.com/rss\n  homepage_url: https://a.com\n  category: bitcoin_core\n  tier: sovereign\n")
    result = svc.sync_from_yaml(db, p)
    assert result.created == 1


def test_activation_toggle(db: Session) -> None:
    svc = SourceRegistryService()
    created = svc.create_source(db, {"name": "X", "slug": "x1", "kind": "rss", "base_url": "https://x.com", "rss_url": "https://x.com/rss", "homepage_url": "https://x.com", "category": "bitcoin_core", "tier": "sovereign", "fetch_interval_minutes": 10})
    svc.disable_source(db, created.id)
    assert svc.get_source(db, created.id) is not None and svc.get_source(db, created.id).is_active is False
