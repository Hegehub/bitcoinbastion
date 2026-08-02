from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.services.access.audit_chain import AccessAuditChain


def test_concurrent_appends_have_unique_sequences_and_valid_head(tmp_path: Path) -> None:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'audit.db'}", connect_args={"check_same_thread": False}
    )
    AccessAuditEvent.__table__.create(engine)

    def append(index: int) -> None:
        with Session(engine) as db:
            AccessAuditChain(db).record_event(
                event_type="wallet_login_success", actor_hash=f"sha256:actor-{index}"
            )
            db.commit()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(append, range(2)))
    with Session(engine) as db:
        rows = list(
            db.execute(
                select(AccessAuditEvent).order_by(AccessAuditEvent.sequence_number)
            ).scalars()
        )
        assert [row.sequence_number for row in rows] == [1, 2]
        assert AccessAuditChain(db).verify_chain_detailed().valid
