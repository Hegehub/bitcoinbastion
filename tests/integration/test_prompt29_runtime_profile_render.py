import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_runtime_profiles_dry_run() -> None:
    for profile in ["compose", "k8s", "k3s", "kind", "minikube", "single-node"]:
        result = subprocess.run(
            [
                sys.executable,
                "deploy/scripts/render-runtime-profile.py",
                "--profile",
                profile,
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr + result.stdout


def test_canonical_kubernetes_overlays_exist() -> None:
    for overlay in ["dev", "staging", "production", "k3s", "kind", "minikube", "single-node"]:
        assert (ROOT / "deploy/kubernetes/overlays" / overlay / "kustomization.yaml").exists()
