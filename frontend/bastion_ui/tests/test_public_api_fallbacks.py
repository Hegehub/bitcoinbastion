from __future__ import annotations

import pytest

pytest.importorskip("reflex")

from bastion_ui.components.public.docs_grid import DOC_CARDS
from bastion_ui.components.public.roadmap_preview import CONSERVATIVE_STATUS_LABELS
from bastion_ui.components.public.status_summary import STATUS_FALLBACK_COPY


def test_status_page_has_safe_fallback_copy() -> None:
    assert "Status temporarily unavailable." in STATUS_FALLBACK_COPY
    assert "cannot verify current backend health" in STATUS_FALLBACK_COPY


def test_roadmap_uses_conservative_status_labels() -> None:
    assert CONSERVATIVE_STATUS_LABELS == (
        "implemented",
        "baseline",
        "experimental",
        "planned",
        "blocked",
        "future",
    )


def test_docs_page_labels_incomplete_docs_as_pending_or_planned() -> None:
    incomplete = {
        title: label
        for title, _body, label in DOC_CARDS
        if title in {"Webhooks", "WebSocket", "SDK", "Production Readiness"}
    }
    assert incomplete == {
        "Webhooks": "pending",
        "WebSocket": "pending",
        "SDK": "planned",
        "Production Readiness": "pending",
    }
