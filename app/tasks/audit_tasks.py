"""Task-compatible entrypoints for canonical Access Audit Chain verification."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.access.audit_chain import AccessAuditChain, AuditChainVerificationResult


def verify_access_security_chain(
    db: Session, *, start_sequence: int | None = None, end_sequence: int | None = None
) -> AuditChainVerificationResult:
    """Verify a bounded segment; scheduling and incident transport stay deployment-specific."""
    return AccessAuditChain(db).verify_chain_detailed(
        start_sequence=start_sequence, end_sequence=end_sequence
    )
