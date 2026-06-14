from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "deploy" / "scripts" / "runtime_profile_lib.py"
RENDER = ROOT / "deploy" / "scripts" / "render-runtime-profile.py"


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_compose_dry_run_renders_commands() -> None:
    lib = load_module(LIB, "runtime_profile_render_compose")
    plan = lib.build_plan("compose", "dev")
    assert "docker compose config" in plan.display_commands
    assert "docker compose --env-file .env up -d --build" in plan.display_commands


def test_k8s_staging_and_production_render_canonical_overlays() -> None:
    lib = load_module(LIB, "runtime_profile_render_k8s")
    staging = lib.build_plan("k8s", "staging")
    production = lib.build_plan("k8s", "production")
    assert staging.overlay_path == "deploy/kubernetes/overlays/staging"
    assert production.overlay_path == "deploy/kubernetes/overlays/production"


def test_runtime_overlay_profiles_render_canonical_paths() -> None:
    lib = load_module(LIB, "runtime_profile_render_overlays")
    expected = {
        "k3s": "deploy/kubernetes/overlays/k3s",
        "kind": "deploy/kubernetes/overlays/kind",
        "minikube": "deploy/kubernetes/overlays/minikube",
        "single-node": "deploy/kubernetes/overlays/single-node",
    }
    for profile, path in expected.items():
        assert lib.build_plan(profile, "local").overlay_path == path


def test_systemd_renders_process_plan() -> None:
    lib = load_module(LIB, "runtime_profile_render_systemd")
    plan = lib.build_plan("bare-metal-systemd", "production")
    rendered = "\n".join(plan.display_commands)
    assert "python -m alembic upgrade head" in rendered
    assert "python -m uvicorn app.main:app" in rendered
    assert "celery -A app.tasks.celery_app.celery_app worker" in rendered


def test_invalid_profile_fails() -> None:
    lib = load_module(LIB, "runtime_profile_render_invalid")
    try:
        lib.build_plan("stratum", "dev")
    except ValueError as exc:
        assert "Unsupported profile" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("invalid profile did not fail")


def test_apply_without_yes_fails(capsys) -> None:
    module = load_module(RENDER, "render_runtime_profile_apply_without_yes")
    assert module.main(["--profile", "k3s", "--env", "staging", "--apply"]) == 1
    assert "Refusing to apply without --yes" in capsys.readouterr().err


def test_missing_overlay_fails_in_validate_mode(monkeypatch, tmp_path, capsys) -> None:
    lib = load_module(LIB, "runtime_profile_render_missing_overlay_lib")
    monkeypatch.setattr(lib, "ROOT", tmp_path)
    plan = lib.CommandPlan("k3s", "staging", [], [], overlay_path="deploy/kubernetes/overlays/k3s", mode="validate")
    assert lib.validate_plan(plan) == 2
    assert "Required overlay missing" in capsys.readouterr().err


def test_dry_run_does_not_execute_apply_commands(monkeypatch) -> None:
    module = load_module(RENDER, "render_runtime_profile_dry_run")
    called = False

    def fake_apply(_plan):
        nonlocal called
        called = True
        return 0

    monkeypatch.setattr(module, "apply_plan", fake_apply)
    assert module.main(["--profile", "k3s", "--env", "staging", "--dry-run"]) == 0
    assert called is False
