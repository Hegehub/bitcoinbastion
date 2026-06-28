from __future__ import annotations

import pytest

pytest.importorskip("reflex")

from pathlib import Path


def test_evidence_route_exists() -> None:
    route_registry = Path(__file__).resolve().parents[1] / "routes" / "__init__.py"
    text = route_registry.read_text()
    assert 'PublicRouteSpec("/evidence"' in text


def test_evidence_page_includes_required_safety_sections() -> None:
    page = Path(__file__).resolve().parents[1] / "routes" / "evidence.py"
    text = page.read_text()
    assert "safety_banner" in text
    assert "source_disagreement_panel" in text
    assert "degraded_evidence_banner" in text
    assert "evidence_limitations_card" in text
