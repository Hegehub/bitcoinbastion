import pytest
from pydantic import ValidationError

from app.storage.evidence.models import (
    EvidenceCheckItem,
    EvidenceStatus,
    StorageEvidence,
    StorageEvidenceType,
)


def test_base_evidence_model_accepts_required_fields() -> None:
    evidence = StorageEvidence(
        evidence_type=StorageEvidenceType.POSTGRES_BACKUP,
        status=EvidenceStatus.PASS,
        environment="test",
        storage_profile="development",
        checks=[EvidenceCheckItem(name="backup_command_present", status=EvidenceStatus.PASS)],
    )

    assert evidence.evidence_type == StorageEvidenceType.POSTGRES_BACKUP
    assert evidence.status == EvidenceStatus.PASS
    assert evidence.repository_component == "storage_layer"


@pytest.mark.parametrize("status", ["pass", "warn", "fail", "skipped", "not_configured"])
def test_allowed_statuses(status: str) -> None:
    assert EvidenceCheckItem(name="status_check", status=status).status == status


def test_check_name_must_not_be_empty() -> None:
    with pytest.raises(ValidationError):
        EvidenceCheckItem(name=" ", status=EvidenceStatus.PASS)
