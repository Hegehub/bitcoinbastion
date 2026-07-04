from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.access import RecoveryAttempt
from app.services.access.recovery_service import AccessRecoveryService, RecoveryError


def _service() -> tuple[AccessRecoveryService, Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, class_=Session)
    db = SessionLocal()
    return AccessRecoveryService(db, server_pepper="pepper", cooldown_seconds=0, max_attempts_per_hour=2), db


def test_no_single_factor_pro_recovery() -> None:
    service, db = _service()
    setup = service.setup_recovery(pass_lookup_hash="hmac-sha256:pass", certificate_fingerprint="sha256:cert", plan_code="pro_pass")
    attempt = service.start_recovery(pass_lookup_hash="hmac-sha256:pass", certificate_fingerprint="sha256:cert", declared_plan_code="pro_pass")
    service.verify_recovery_factor(recovery_attempt_id=attempt.recovery_attempt_id, factor_type="recovery_phrase_24", recovery_factor=" ".join(setup.phrase_words))
    try:
        service.complete_recovery(recovery_attempt_id=attempt.recovery_attempt_id)
    except RecoveryError as exc:
        assert str(exc) == "quorum_incomplete"
    else:  # pragma: no cover
        raise AssertionError("single-factor Pro recovery succeeded")
    db.close()


def test_failed_attempts_are_rate_limited_and_locked() -> None:
    service, db = _service()
    service.setup_recovery(pass_lookup_hash="hmac-sha256:pass", certificate_fingerprint=None, plan_code="lite_pass")
    attempt = service.start_recovery(pass_lookup_hash="hmac-sha256:pass", declared_plan_code="lite_pass")
    for _ in range(2):
        try:
            service.verify_recovery_factor(recovery_attempt_id=attempt.recovery_attempt_id, factor_type="recovery_phrase_12", recovery_factor="wrong phrase with twelve words maybe but invalid")
        except RecoveryError:
            pass
    stored = db.execute(select(RecoveryAttempt).where(RecoveryAttempt.attempt_hash == attempt.recovery_attempt_id)).scalar_one()
    assert stored.status == "locked"
    db.close()
