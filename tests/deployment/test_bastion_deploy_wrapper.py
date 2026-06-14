from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / "deploy" / "scripts" / "bastion-deploy"


def load_wrapper() -> ModuleType:
    loader = importlib.machinery.SourceFileLoader("bastion_deploy_wrapper", str(WRAPPER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[loader.name] = module
    loader.exec_module(module)
    return module


def test_detect_command_delegates_to_detection_script(monkeypatch) -> None:
    module = load_wrapper()
    commands: list[list[str]] = []
    monkeypatch.setattr(module, "run_child", lambda command: commands.append(command) or 0)
    assert module.main(["detect"]) == 0
    assert str(module.DETECT) in commands[0]


def test_render_command_uses_dry_run(monkeypatch) -> None:
    module = load_wrapper()
    commands: list[list[str]] = []
    monkeypatch.setattr(module, "run_child", lambda command: commands.append(command) or 0)
    assert module.main(["render", "--profile", "k3s", "--env", "staging"]) == 0
    assert "--dry-run" in commands[0]


def test_validate_command_uses_validate_mode(monkeypatch) -> None:
    module = load_wrapper()
    commands: list[list[str]] = []
    monkeypatch.setattr(module, "run_child", lambda command: commands.append(command) or 0)
    assert module.main(["validate", "--profile", "k3s", "--env", "staging"]) == 0
    assert "--validate" in commands[0]


def test_apply_requires_yes(capsys) -> None:
    module = load_wrapper()
    assert module.main(["apply", "--profile", "k3s", "--env", "staging"]) == 1
    assert "Refusing to apply without --yes" in capsys.readouterr().err


def test_apply_delegates_with_apply_and_yes(monkeypatch) -> None:
    module = load_wrapper()
    commands: list[list[str]] = []
    monkeypatch.setattr(module, "run_child", lambda command: commands.append(command) or 0)
    assert module.main(["apply", "--profile", "k3s", "--env", "staging", "--yes"]) == 0
    assert "--apply" in commands[0]
    assert "--yes" in commands[0]


def test_wrapper_returns_nonzero_when_child_fails(monkeypatch) -> None:
    module = load_wrapper()
    monkeypatch.setattr(module, "run_child", lambda _command: 4)
    assert module.main(["render", "--profile", "k3s", "--env", "staging"]) == 4
