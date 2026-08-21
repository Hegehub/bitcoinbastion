from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.bastion_trace import TraceReport
from app.services.bastion_trace.graph.api_projection import TraceGraphApiProjectionService
from app.services.bastion_trace.graph.persistence import TraceGraphSnapshotRepository


def test_graph_snapshot_survives_session_and_engine_restart(tmp_path: Path) -> None:
    database = tmp_path / "trace-snapshots.sqlite"
    url = f"sqlite+pysqlite:///{database}"
    engine = create_engine(url, future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        report = TraceReport(
            address="bc1qexampleaddress0000000000000000000000000",
            chain="bitcoin",
            trace_score=0.1,
            trace_band="LOW",
            confidence=0.8,
            source_quality="MEDIUM",
            freshness="FRESH",
            summary="immutable capture",
        )
        session.add(report)
        session.commit()
        session.refresh(report)
        report_id = report.id
        graph = TraceGraphApiProjectionService().graph_for_report_model(report)
        captured = TraceGraphSnapshotRepository(session).capture(report.id, graph)
        snapshot_id = captured.snapshot.snapshot_id
        expected = captured.model_dump(mode="json")
    engine.dispose()

    restarted = create_engine(url, future=True)
    with Session(restarted) as session:
        restored = TraceGraphSnapshotRepository(session).exact(report_id, snapshot_id)
        assert restored is not None
        assert restored.model_dump(mode="json") == expected
        assert TraceGraphSnapshotRepository(session).capture(report_id, restored).snapshot.snapshot_id == snapshot_id
    restarted.dispose()
