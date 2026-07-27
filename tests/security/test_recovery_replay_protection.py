from pathlib import Path


def test_replay_references_are_persisted_in_capsule_metadata() -> None:
    source = Path("app/services/wallet_auth/recovery/capsule.py").read_text()
    assert '"replay_references"' in source and 'revocation["replay_used"]' in source
