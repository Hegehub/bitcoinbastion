from __future__ import annotations

from bastion_ui.domain.operations.models import IntelligenceHealthViewModel
from bastion_ui.transport.generated_http import IntelligenceHealthIntelligenceGetSuccess


def adapt_intelligence_health(
    response: IntelligenceHealthIntelligenceGetSuccess,
) -> IntelligenceHealthViewModel:
    payload = response.root
    return IntelligenceHealthViewModel(
        status=payload.status,
        degraded=payload.degraded_state,
        provider_confidence=payload.provider_confidence,
        last_success=payload.last_success,
        last_failure=payload.last_failure,
        limitations=(
            tuple(payload.operational_limitations)
            if payload.operational_limitations is not None
            else None
        ),
    )
