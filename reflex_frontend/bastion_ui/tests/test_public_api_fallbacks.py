from __future__ import annotations

from bastion_ui.components.public.docs_grid import DOC_CARDS
from bastion_ui.components.public.roadmap_preview import CONSERVATIVE_ROADMAP_STATUSES, ROADMAP_ROWS
from bastion_ui.components.public.status_summary import STATUS_FALLBACK_COPY


def test_roadmap_uses_conservative_status_labels() -> None:
    allowed = set(CONSERVATIVE_ROADMAP_STATUSES)
    assert allowed == {"implemented", "baseline", "experimental", "planned", "blocked", "future"}
    assert {row["Status"] for row in ROADMAP_ROWS} <= allowed


def test_docs_page_does_not_claim_missing_docs_are_complete() -> None:
    status_by_title = {title: status for title, _description, status in DOC_CARDS}
    assert status_by_title["Webhooks"] == "pending"
    assert status_by_title["WebSocket"] == "pending"
    assert status_by_title["Production Readiness"] == "pending"


def test_status_fallback_does_not_fake_live_status() -> None:
    assert "temporarily unavailable" in STATUS_FALLBACK_COPY
    assert "cannot verify current backend health" in STATUS_FALLBACK_COPY
