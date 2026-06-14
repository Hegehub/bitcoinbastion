from pathlib import Path

from bastion_ui.security.safety_copy import FORBIDDEN_WORDING, REQUIRED_SAFETY_COPY

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SOURCES = [
    ROOT / "routes" / "home.py",
    ROOT / "routes" / "platform.py",
    ROOT / "routes" / "developers.py",
    ROOT / "routes" / "operations.py",
    ROOT / "routes" / "manifesto.py",
    ROOT / "routes" / "evidence.py",
    ROOT / "routes" / "status.py",
    ROOT / "routes" / "roadmap.py",
    ROOT / "routes" / "security.py",
    ROOT / "routes" / "docs.py",
    ROOT / "components" / "ui" / "safety_banner.py",
]


def test_safety_copy_includes_required_language() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_SOURCES)
    required = (
        "No custody",
        "Advisory-only",
        "Not legal verification",
        "Not Bitcoin consensus proof",
        "Never enter seed phrases",
        "private keys",
        "wallet files",
    )
    for phrase in required:
        assert phrase in combined or any(phrase in copy for copy in REQUIRED_SAFETY_COPY)


def test_forbidden_wording_is_absent_from_public_pages() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in PUBLIC_SOURCES)
    for phrase in FORBIDDEN_WORDING:
        assert phrase not in combined
