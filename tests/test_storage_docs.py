from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"


def _read_doc(name: str) -> str:
    path = DOCS / name
    assert path.exists(), f"missing storage documentation: {path}"
    return path.read_text(encoding="utf-8")


def test_storage_runbook_contains_required_operational_sections() -> None:
    text = _read_doc("STORAGE_LAYER_RUNBOOK.md")

    required_sections = [
        "# Bitcoin Bastion Storage Layer Runbook",
        "## 1. Purpose",
        "## 2. Storage Components",
        "## 3. Normal Operating Mode",
        "## 4. Startup Checks",
        "## 5. Health Checks",
        "## 6. Storage Status Endpoint",
        "## 7. Common Failure Scenarios",
        "## 8. Degraded Mode Behavior",
        "## 9. Outbox Operations",
        "## 10. Object Storage Operations",
        "## 11. Redis Loss Scenario",
        "## 12. PostgreSQL Degradation Scenario",
        "## 13. Artifact Integrity Validation",
        "## 14. Operator Commands",
        "## 15. Escalation Rules",
        "## 16. Known Limitations",
    ]

    for section in required_sections:
        assert section in text

    critical_phrases = [
        "PostgreSQL is the source of truth",
        "Redis is not a source of truth",
        "Object Storage stores artifact bytes",
        "SHA-256",
        "degraded mode",
        "No seed phrases",
        "Bitcoin private keys",
        "outbox",
    ]

    for phrase in critical_phrases:
        assert phrase in text


def test_storage_backup_recovery_contains_restore_drill_and_evidence_contract() -> None:
    text = _read_doc("STORAGE_BACKUP_RECOVERY.md")

    required_sections = [
        "# Bitcoin Bastion Storage Backup and Recovery",
        "## 1. Purpose",
        "## 2. Recovery Objectives",
        "## 3. PostgreSQL Backup Strategy",
        "## 4. PostgreSQL Restore Strategy",
        "## 5. Redis Recovery Strategy",
        "## 6. Object Storage Backup Strategy",
        "## 7. Object Storage Restore Strategy",
        "## 8. Artifact Integrity Checks",
        "## 9. Outbox Replay Strategy",
        "## 10. Restore Drill Procedure",
        "## 11. Evidence Generation",
        "## 12. Recovery Acceptance Criteria",
        "## 13. Future Storage Engines",
        "## 14. Known Risks",
    ]

    for section in required_sections:
        assert section in text

    required_phrases = [
        "PITR",
        "WAL archive",
        "restore drill",
        "Redis is not a source of truth",
        "SHA-256",
        "storage_backup_evidence.json",
        "storage_restore_evidence.json",
        "object_storage_integrity_evidence.json",
        "outbox_replay_evidence.json",
        "not `pass`",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_storage_production_checklist_covers_security_privacy_and_degraded_mode() -> None:
    text = _read_doc("STORAGE_PRODUCTION_CHECKLIST.md")

    required_sections = [
        "# Bitcoin Bastion Storage Production Checklist",
        "## 1. Purpose",
        "## 2. Scope",
        "## 3. Environment Configuration",
        "## 4. PostgreSQL Readiness",
        "## 5. Redis Readiness",
        "## 6. Object Storage Readiness",
        "## 7. Outbox Readiness",
        "## 8. Security Checklist",
        "## 9. Privacy Checklist",
        "## 10. Backup and Restore Checklist",
        "## 11. Observability Checklist",
        "## 12. Degraded Mode Checklist",
        "## 13. Release Gate Checklist",
        "## 14. Rollback Checklist",
        "## 15. Signoff",
    ]

    for section in required_sections:
        assert section in text

    required_checklist_items = [
        "- [ ] No seed phrases stored.",
        "- [ ] No Bitcoin private keys stored.",
        "- [ ] No wallet files stored.",
        "- [ ] No xprv/yprv/zprv stored.",
        "- [ ] No raw secrets in logs.",
        "- [ ] No Redis-only critical state.",
        "- [ ] No public object storage bucket for evidence artifacts.",
        "- [ ] No route handler directly writes to multiple storage engines.",
        "- [ ] No global user_id introduced for privacy-sensitive domains.",
        "PostgreSQL down → API not ready for critical operations.",
        "Object Storage down → artifact upload/download unavailable; metadata still protected.",
    ]

    for item in required_checklist_items:
        assert item in text


def test_storage_architecture_links_operational_runbooks() -> None:
    text = _read_doc("STORAGE_LAYER_ARCHITECTURE.md")

    assert "docs/STORAGE_LAYER_RUNBOOK.md" in text
    assert "docs/STORAGE_BACKUP_RECOVERY.md" in text
    assert "docs/STORAGE_PRODUCTION_CHECKLIST.md" in text
    assert "do not claim production readiness" in text.lower()
