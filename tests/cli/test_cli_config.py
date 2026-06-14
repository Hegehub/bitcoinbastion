from __future__ import annotations

from cli.bastion_cli.config import CLIConfig


def test_global_config_reads_env_vars(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("BB_API_BASE_URL", "http://env.example")
    monkeypatch.setenv("BB_API_TOKEN", "env-token")
    monkeypatch.setenv("BB_REQUEST_TIMEOUT_SECONDS", "9")
    monkeypatch.setenv("BB_CLI_OUTPUT", "json")

    config = CLIConfig.from_env()

    assert config.api_base_url == "http://env.example"
    assert config.token == "env-token"
    assert config.timeout == 9
    assert config.output == "json"


def test_global_flags_override_env_vars(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("BB_API_BASE_URL", "http://env.example")
    config = CLIConfig.from_env(api_base_url="http://flag.example", token="flag-token", timeout=2, output="table")

    assert config.api_base_url == "http://flag.example"
    assert config.token == "flag-token"
    assert config.timeout == 2
    assert config.output == "table"
