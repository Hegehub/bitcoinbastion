import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.event_outbox import EventOutbox
from app.db.repositories.bastion_trace_repository import BastionTraceRepository
from app.schemas.bastion_trace import BastionTraceTreasuryCheckRequest
from app.services.bastion_trace.trace_service import TraceService

_VALID_ADDRESS = "bc1qexampleaddress0000000000000000000000000"


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_trace_report_creation_emits_advisory_outbox_event() -> None:
    with _session() as db:
        report = TraceService(BastionTraceRepository(db)).analyze_address(_VALID_ADDRESS)

        event = db.query(EventOutbox).filter_by(event_type="trace.report.created").one()
        payload = json.loads(event.payload_json)
        assert payload["report_id"] == report.id
        assert payload["advisory_not_legal_verdict"] is True
        assert payload["not_consensus_proof"] is True
        assert payload["no_custody"] is True
        assert event.aggregate_type == "trace_report"


def test_trace_treasury_destination_check_emits_outbox_event() -> None:
    with _session() as db:
        result = TraceService(BastionTraceRepository(db)).treasury_destination_check(
            BastionTraceTreasuryCheckRequest(destination_address=_VALID_ADDRESS)
        )

        event = (
            db.query(EventOutbox)
            .filter_by(event_type="trace.treasury_destination_check.created")
            .one()
        )
        payload = json.loads(event.payload_json)
        assert payload["report_id"] == result["trace_report_id"]
        assert payload["advisory_not_legal_verdict"] is True
        assert payload["no_custody"] is True
