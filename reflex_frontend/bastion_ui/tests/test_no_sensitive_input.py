from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_PROMPTS = (
    "enter your seed",
    "please enter seed",
    "enter your private key",
    "upload wallet.dat",
    "upload keystore",
    "paste xprv",
    "paste yprv",
    "paste zprv",
    "signing material input",
)


def test_evidence_and_proof_packet_ui_do_not_request_sensitive_material() -> None:
    files = list((ROOT / "components/evidence").glob("*.py")) + [ROOT / "routes" / "evidence.py"]
    for path in files:
        text = path.read_text().lower()
        for prompt in SENSITIVE_PROMPTS:
            assert prompt not in text, f"{prompt!r} found in {path}"


def test_no_new_evidence_input_fields_are_added() -> None:
    evidence_component_text = "\n".join(
        path.read_text() for path in (ROOT / "components/evidence").glob("*.py")
    )
    assert "rx.input" not in evidence_component_text
