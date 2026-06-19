from __future__ import annotations

from pathlib import Path

SCAN_ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_PROMPTS = (
    "input seed phrase",
    "input mnemonic",
    "input private key",
    "upload wallet.dat",
    "upload keystore",
    "paste signing material",
)


def test_evidence_and_proof_packet_ui_do_not_request_sensitive_material() -> None:
    offenders: list[str] = []
    for relative in ("routes/evidence.py", "routes/proof_packet.py", "components/evidence"):
        path = SCAN_ROOT / relative
        files = path.rglob("*.py") if path.is_dir() else [path]
        for file_path in files:
            text = file_path.read_text(encoding="utf-8", errors="ignore").casefold()
            for phrase in SENSITIVE_PROMPTS:
                if phrase in text:
                    offenders.append(f"{file_path.relative_to(SCAN_ROOT)}:{phrase}")
    assert offenders == []
