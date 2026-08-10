from __future__ import annotations

from datetime import UTC, datetime

from bastion_ui.domain.overview.models import PublicStatusViewModel
from bastion_ui.domain.provenance import Provenance, ProvenanceState
from bastion_ui.transport.generated_http import PublicStatusApiV1PublicStatusGetSuccess


def adapt_public_status(
    response: PublicStatusApiV1PublicStatusGetSuccess,
    *,
    observed_at: datetime | None = None,
) -> PublicStatusViewModel:
    payload = response.root.data
    return PublicStatusViewModel(
        platform_status=payload.platform_status,
        trace_status=payload.trace_status,
        production_calibrated=payload.production_calibrated,
        modules=tuple(sorted(payload.modules.items())),
        known_limitations=(
            tuple(payload.known_limitations) if payload.known_limitations is not None else None
        ),
        last_update=payload.last_update,
        provenance=Provenance(
            state=ProvenanceState.LIVE,
            source_label="Bitcoin Bastion public status API",
            observed_at=observed_at or datetime.now(UTC),
            limitation="Runtime status is informational and does not prove consensus truth.",
        ),
    )
