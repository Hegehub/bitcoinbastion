from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = (
    "clean address",
    "dirty address",
    "criminal address",
    "guaranteed safe",
    "approved payment",
    "verified illicit",
)
SENSITIVE = ("seed phrase", "mnemonic", "private key", "xprv", "yprv", "zprv", "wallet.dat", "keystore", "signing material")


def test_forbidden_wow_wording_absent() -> None:
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in (ROOT / "components" / "wow").glob("*.py"))
    for phrase in FORBIDDEN:
        assert phrase not in text


def test_sensitive_material_only_appears_in_never_enter_safety_copy() -> None:
    for path in (ROOT / "components" / "wow").glob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            lowered = line.lower()
            if any(term in lowered for term in SENSITIVE):
                assert "never enter" in lowered or "do not request" in lowered or "no custody" in lowered
