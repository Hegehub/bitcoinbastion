import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "deploy" / "scripts"
SUPPORTED = ["compose", "k8s", "k3s", "kind", "minikube", "single-node", "bare-metal-systemd"]


def test_runtime_profile_scripts_exist() -> None:
    assert (SCRIPTS / "detect-runtime-profile.py").exists()
    assert (SCRIPTS / "render-runtime-profile.py").exists()
    assert (SCRIPTS / "bastion-deploy").exists()


def test_python_runtime_scripts_are_syntactically_valid() -> None:
    for filename in ("detect-runtime-profile.py", "render-runtime-profile.py", "runtime_profile_lib.py"):
        py_compile.compile(str(SCRIPTS / filename), doraise=True)


def test_bastion_deploy_has_shebang_and_supported_profiles() -> None:
    text = (SCRIPTS / "bastion-deploy").read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env python3")
    assert "--profile" in text
    for profile in SUPPORTED:
        assert profile in (SCRIPTS / "runtime_profile_lib.py").read_text(encoding="utf-8")
