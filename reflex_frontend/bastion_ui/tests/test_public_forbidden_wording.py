from __future__ import annotations

from pathlib import Path

PUBLIC_PATHS = (
    Path("reflex_frontend/bastion_ui/routes"),
    Path("reflex_frontend/bastion_ui/components/public"),
)
FORBIDDEN_PARTS = (
    ("clean", "address"),
    ("dirty", "address"),
    ("criminal", "address"),
    ("guaranteed", "safe"),
    ("approved", "payment"),
    ("verified", "illicit"),
)


def test_forbidden_wording_absent_from_public_routes_and_components() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for root in PUBLIC_PATHS
        for path in root.rglob("*.py")
        if path.name != "test_public_forbidden_wording.py"
    ).lower()
    for left, right in FORBIDDEN_PARTS:
        assert f"{left} {right}" not in text
