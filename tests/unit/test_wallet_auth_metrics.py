from prometheus_client import generate_latest

from app.services.wallet_auth.metrics import WalletMetrics


def test_wallet_metrics_normalize_untrusted_labels_without_identifiers() -> None:
    metrics = WalletMetrics()
    secret = "bc1q-private-looking-identifier"
    metrics.proof(
        action=secret,
        proof_type=secret,
        verification_strength=secret,
        network=secret,
        result="unexpected-result",
        reason_code="arbitrary exception with id",
    )
    output = generate_latest().decode()
    sample = next(
        line
        for line in output.splitlines()
        if line.startswith("wallet_auth_proofs_total{") and 'action="unknown"' in line
    )
    assert 'proof_type="unknown"' in sample and 'reason_code="unknown"' in sample
    assert secret not in sample


def test_endpoint_group_is_bounded() -> None:
    metrics = WalletMetrics()
    metrics.pop_request(
        actor_type="bitcoin_wallet_principal",
        endpoint="not-a-group/12345",
        result="success",
        reason_code="unknown",
    )
    output = generate_latest().decode()
    assert 'endpoint_group="unknown"' in output
    assert "12345" not in next(
        line
        for line in output.splitlines()
        if line.startswith("wallet_pop_request_verifications_total{")
    )
