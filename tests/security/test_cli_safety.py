from pathlib import Path


def test_cli_does_not_expose_signing_or_broadcast_commands() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in Path("cli/bastion_cli").rglob("*.py"))
    output = source.casefold()
    assert "sign transaction" not in output
    assert "broadcast transaction" not in output
    assert "private key command" not in output


def test_trace_help_preserves_safety_copy() -> None:
    source = Path("cli/bastion_cli/commands/trace.py").read_text(encoding="utf-8").casefold()
    assert "advisory" in source or "public bitcoin addresses" in source
