from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.access.recovery_seed import recovery_phrase_commitment, reject_bitcoin_wallet_seed_warning

SEED_12 = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
SEED_24 = (
    "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon "
    "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art"
)
WIF = "KwdMAj2BGe2M4A4V2xY7dUQmP5xwVvFghm7N6fYB3GdQ2g8U9zQ1"
XPRV = "xprv9s21ZrQH143K3exampleprivatekeymaterialbitcoinwallet"
DESCRIPTOR = "wpkh([d34db33f/84h/0h/0h]xprv9s21ZrQH143K3example/0/*)"


@pytest.mark.parametrize("secret", [SEED_12, SEED_24, WIF, XPRV, DESCRIPTOR])
def test_bitcoin_wallet_material_not_accepted_for_access_recovery(secret: str) -> None:
    with pytest.raises(ValueError):
        reject_bitcoin_wallet_seed_warning(secret)


def test_recovery_commitment_rejects_seed_like_phrase() -> None:
    with pytest.raises(ValueError) as exc_info:
        recovery_phrase_commitment(SEED_12, "pepper")

    assert str(exc_info.value) == "bitcoin_seed_input_rejected"


def test_recovery_endpoint_rejects_seed_like_factor_without_creating_session() -> None:
    response = TestClient(app).post(
        "/api/v1/access/recovery/factors",
        json={
            "recovery_attempt_id": "attempt-test",
            "factor_type": "recovery_phrase_12",
            "recovery_factor": SEED_12,
        },
    )

    assert response.status_code in {400, 422, 503}
    assert "session_token" not in response.text
    assert SEED_12 not in response.text


def test_frontend_and_docs_include_bitcoin_seed_safety_copy() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in [
            Path("docs/ACCESS_RECOVERY.md"),
            Path("reflex_frontend/bastion_ui/routes/access.py"),
        ]
        if path.exists()
    )

    assert "Bastion Recovery Seed is not your Bitcoin wallet seed" in text
    assert "Bastion will never ask for your Bitcoin" in text


def test_sdks_do_not_export_seed_auth_helpers() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for root in [Path("sdk/python/bitcoin_bastion_sdk"), Path("sdk/typescript/src")]
        for path in root.rglob("*")
        if path.suffix in {".py", ".ts"}
    ).lower()

    forbidden = ["importbitcoinseed", "authwithseed", "loginwithseed", "walletseedlogin"]
    assert all(name not in combined for name in forbidden)
