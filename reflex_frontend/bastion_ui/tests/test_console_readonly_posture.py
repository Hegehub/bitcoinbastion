from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTE_TEXT = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "routes").glob("console*.py"))


def test_console_readonly_advisory_no_custody_posture() -> None:
    required = (
        "Read-only preview",
        "Operator review required",
        "Evidence-based",
        "Advisory-only",
        "No custody",
        "No private key or seed phrase handling",
        "Degraded, fallback, stale, and unavailable states must remain visible",
    )
    for phrase in required:
        assert phrase in ROUTE_TEXT


def test_console_forbidden_claims_absent() -> None:
    forbidden = (
        "clean address",
        "dirty address",
        "criminal address",
        "guaranteed safe",
        "approved payment",
        "verified illicit",
        "guaranteed profit",
        "price prediction",
        "automatic trading",
        "fully autonomous treasury execution",
        "legal verification",
        "Bitcoin consensus proof",
    )
    lowered = ROUTE_TEXT.lower()
    for phrase in forbidden:
        assert phrase.lower() not in lowered
