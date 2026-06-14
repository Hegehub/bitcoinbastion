from pathlib import Path


def test_typescript_examples_are_bounded_and_advisory() -> None:
    examples = Path("sdk/typescript/examples")
    assert (examples / "subscribe-events.ts").exists()
    combined = "\n".join(path.read_text(encoding="utf-8") for path in examples.glob("*.ts"))
    lowered = combined.casefold()
    assert "private key" not in lowered
    assert "seed phrase" not in lowered
    assert "buy signal" not in lowered
    assert "guaranteed" not in lowered


def test_typescript_webhook_helper_documents_replay_fields() -> None:
    readme = Path("sdk/typescript/README.md").read_text(encoding="utf-8")
    webhooks = Path("sdk/typescript/src/webhooks.ts").read_text(encoding="utf-8")
    assert "X-Bastion-Delivery-ID" in readme or "delivery" in webhooks
    assert "timingSafeEqual" in webhooks
