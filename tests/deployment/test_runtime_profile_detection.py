from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "deploy" / "scripts" / "runtime_profile_lib.py"
DETECT = ROOT / "deploy" / "scripts" / "detect-runtime-profile.py"


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_detects_missing_tools_without_failing(monkeypatch) -> None:
    lib = load_module(LIB, "runtime_profile_lib_missing")
    monkeypatch.setattr(lib.shutil, "which", lambda _name: None)
    monkeypatch.setattr(lib, "detect_ram_gb", lambda: None)
    result = lib.detect_environment()
    assert result["recommendation"]["profile"] == "manual-review"
    assert result["tools"]["docker"] is False
    assert result["tools"]["kubectl"] is False


def test_recommends_k3s_when_k3s_exists(monkeypatch) -> None:
    lib = load_module(LIB, "runtime_profile_lib_k3s")
    monkeypatch.setattr(lib, "command_exists", lambda name: name == "k3s")
    monkeypatch.setattr(lib, "detect_docker_compose", lambda: False)
    monkeypatch.setattr(lib, "get_kubectl_context", lambda: None)
    monkeypatch.setattr(lib, "detect_ram_gb", lambda: 8.0)
    result = lib.detect_environment()
    assert result["recommendation"]["profile"] == "k3s"


def test_recommends_k8s_when_kubectl_context_exists(monkeypatch) -> None:
    lib = load_module(LIB, "runtime_profile_lib_k8s")
    monkeypatch.setattr(lib, "command_exists", lambda name: name == "kubectl")
    monkeypatch.setattr(lib, "detect_docker_compose", lambda: False)
    monkeypatch.setattr(lib, "get_kubectl_context", lambda: "dev-cluster")
    monkeypatch.setattr(lib, "detect_ram_gb", lambda: 16.0)
    result = lib.detect_environment()
    assert result["recommendation"]["profile"] == "k8s"


def test_recommends_kind_in_ci_when_kind_exists(monkeypatch) -> None:
    lib = load_module(LIB, "runtime_profile_lib_kind_ci")
    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr(lib, "command_exists", lambda name: name == "kind")
    monkeypatch.setattr(lib, "detect_docker_compose", lambda: False)
    monkeypatch.setattr(lib, "detect_ram_gb", lambda: 4.0)
    result = lib.detect_environment()
    assert result["recommendation"]["profile"] == "kind"


def test_recommends_compose_when_only_docker_compose_exists(monkeypatch) -> None:
    lib = load_module(LIB, "runtime_profile_lib_compose")
    monkeypatch.setattr(lib, "command_exists", lambda _name: False)
    monkeypatch.setattr(lib, "detect_docker_compose", lambda: True)
    monkeypatch.setattr(lib, "detect_ram_gb", lambda: 4.0)
    result = lib.detect_environment()
    assert result["recommendation"]["profile"] == "compose"


def test_recommends_systemd_when_only_systemd_exists(monkeypatch) -> None:
    lib = load_module(LIB, "runtime_profile_lib_systemd")
    monkeypatch.setattr(lib, "command_exists", lambda _name: False)
    monkeypatch.setattr(lib, "detect_docker_compose", lambda: False)
    monkeypatch.setattr(lib, "is_systemd_available", lambda: True)
    monkeypatch.setattr(lib, "detect_ram_gb", lambda: 2.5)
    result = lib.detect_environment()
    assert result["recommendation"]["profile"] == "bare-metal-systemd"


def test_handles_unknown_ram(monkeypatch) -> None:
    lib = load_module(LIB, "runtime_profile_lib_unknown_ram")
    monkeypatch.setattr(lib, "detect_ram_gb", lambda: None)
    warning = lib.resource_warnings({"ram_gb": None})[0]
    assert "RAM size unknown" in warning


def test_json_output_shape_is_stable(monkeypatch, capsys) -> None:
    module = load_module(DETECT, "detect_runtime_profile_script")
    monkeypatch.setattr(
        module,
        "detect_environment",
        lambda: {
            "tools": {"docker": False, "docker_compose": False, "kubectl": False, "k3s": False, "kind": False, "minikube": False, "systemd": False},
            "system": {"cpu_count": 4, "ram_gb": None, "ci": False, "platform": "linux", "kubectl_context": None},
            "recommendation": {"profile": "manual-review", "reason": "test", "warnings": []},
        },
    )
    assert module.main(["--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert set(data) == {"tools", "system", "recommendation"}
    assert data["recommendation"]["profile"] == "manual-review"
