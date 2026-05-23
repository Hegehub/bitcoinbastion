from app.schemas.bastion_trace import LegalHoldStatus


def is_active(status: str) -> bool:
    return status == LegalHoldStatus.ACTIVE.value
