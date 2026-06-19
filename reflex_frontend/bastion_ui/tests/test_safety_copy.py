from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAFETY_ROOT = ROOT / "components" / "safety"


def test_required_safety_copy_exists() -> None:
    text = "\n".join(path.read_text() for path in SAFETY_ROOT.glob("*.py"))
    for required in [
        "Advisory-only.",
        "Not legal verification.",
        "Not Bitcoin consensus proof.",
        "No custody.",
        "Public Bitcoin addresses only.",
        "Never enter seed phrases, private keys, wallet files or signing material.",
    ]:
        assert required in text
