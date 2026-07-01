from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = (ROOT / "Makefile").read_text(encoding="utf-8")
TARGETS = [
    "runtime-profiles",
    "runtime-detect",
    "runtime-render-compose",
    "runtime-render-k8s",
    "runtime-render-k3s",
    "runtime-render-kind",
    "runtime-render-minikube",
    "runtime-render-single-node",
    "deploy-compose",
    "deploy-k8s",
    "deploy-k3s",
    "deploy-kind",
    "deploy-minikube",
    "deploy-single-node",
    "systemd-notes",
]


def body(target: str) -> str:
    match = re.search(rf"^{re.escape(target)}:\n(?P<body>(?:\t.*\n)+)", MAKEFILE, re.MULTILINE)
    assert match, f"missing target body: {target}"
    return match.group("body")


def test_runtime_targets_exist() -> None:
    for target in TARGETS:
        assert f"{target}:" in MAKEFILE


def test_runtime_targets_are_phony() -> None:
    phony = next(line for line in MAKEFILE.splitlines() if line.startswith(".PHONY:"))
    for target in TARGETS:
        assert target in phony


def test_runtime_targets_call_real_scripts_or_commands() -> None:
    for target in TARGETS:
        target_body = body(target)
        assert 'echo "Runtime detected"' not in target_body
        assert any(
            token in target_body
            for token in (
                "deploy/scripts/",
                "kubectl ",
                "docker compose",
                "cat docs/BARE_METAL_SYSTEMD.md",
            )
        ), target


def test_runtime_render_targets_reference_expected_profiles_and_paths() -> None:
    assert "--profile compose" in body("runtime-render-compose")
    assert "--profile k8s" in body("runtime-render-k8s")
    assert "--profile k3s" in body("runtime-render-k3s")
    assert "--profile kind" in body("runtime-render-kind")
    assert "--profile minikube" in body("runtime-render-minikube")
    assert "--profile single-node" in body("runtime-render-single-node")
    assert "deploy/kubernetes/overlays/production" in MAKEFILE or "--profile k8s" in MAKEFILE
