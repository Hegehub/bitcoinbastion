from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
K3S_DIR = ROOT / "deploy" / "kubernetes" / "overlays" / "k3s"
SINGLE_NODE_DIR = ROOT / "deploy" / "kubernetes" / "overlays" / "single-node"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_k3s_overlay_files_exist() -> None:
    expected = {
        "kustomization.yaml",
        "namespace.yaml",
        "patch-env.yaml",
        "patch-resources.yaml",
        "patch-ingress-traefik.yaml",
        "patch-single-node-replicas.yaml",
        "README.md",
    }
    assert expected == {path.name for path in K3S_DIR.iterdir()}


def test_single_node_overlay_files_exist() -> None:
    expected = {
        "kustomization.yaml",
        "namespace.yaml",
        "patch-env.yaml",
        "patch-resources.yaml",
        "patch-single-node-replicas.yaml",
        "patch-disable-heavy-jobs.yaml",
        "patch-disable-hpa.yaml",
        "README.md",
    }
    assert expected == {path.name for path in SINGLE_NODE_DIR.iterdir()}


def test_overlay_kustomizations_reference_base_and_namespaces() -> None:
    k3s = read(K3S_DIR / "kustomization.yaml")
    single_node = read(SINGLE_NODE_DIR / "kustomization.yaml")
    assert "../../base" in k3s
    assert "namespace: bitcoin-bastion-k3s" in k3s
    assert "patch-ingress-traefik.yaml" in k3s
    assert "../../base" in single_node
    assert "namespace: bitcoin-bastion-single-node" in single_node
    assert "patch-disable-heavy-jobs.yaml" in single_node
    assert "patch-disable-hpa.yaml" in single_node


def test_k3s_readme_documents_traefik_storage_and_no_custody() -> None:
    content = read(K3S_DIR / "README.md").lower()
    assert "k3s is recommended for sovereign small deployments" in content
    assert "traefik" in content
    assert "local-path" in content
    assert "not production-equal" in content
    assert "no custody" in content
    assert "seed phrase" in content
    assert "private key" in content
    assert "signing material" in content


def test_single_node_readme_documents_non_ha_and_safety() -> None:
    content = read(SINGLE_NODE_DIR / "README.md").lower()
    assert "not highly available" in content
    assert "must not be presented as equivalent to full production kubernetes" in content
    assert "not equivalent to a production cluster" in content
    assert "no custody" in content
    assert "seed phrase" in content
    assert "private key" in content
    assert "signing material" in content


def test_single_node_patches_suspend_real_heavy_cronjobs_and_neutralize_hpa() -> None:
    patch = read(SINGLE_NODE_DIR / "patch-disable-heavy-jobs.yaml")
    assert "name: bitcoin-bastion-recovery-drill" in patch
    assert "name: bitcoin-bastion-evidence-generate-packets" in patch
    assert "name: bitcoin-bastion-intelligence-refresh-similarity" in patch
    assert patch.count("suspend: true") >= 3
    hpa = read(SINGLE_NODE_DIR / "patch-disable-hpa.yaml")
    assert "kind: HorizontalPodAutoscaler" in hpa
    assert "minReplicas: 1" in hpa
    assert "maxReplicas: 1" in hpa


def test_runtime_profile_metadata_references_new_overlays() -> None:
    k3s = read(ROOT / "deploy" / "runtime-profiles" / "k3s.yaml")
    single_node = read(ROOT / "deploy" / "runtime-profiles" / "single-node.yaml")
    assert "status: overlay-added" in k3s
    assert "deploy/kubernetes/overlays/k3s" in k3s
    assert "status: overlay-added" in single_node
    assert "deploy/kubernetes/overlays/single-node" in single_node


@pytest.mark.skipif(shutil.which("kubectl") is None, reason="kubectl is not installed")
@pytest.mark.parametrize("overlay", ["k3s", "single-node"])
def test_overlays_render_with_kubectl_when_available(overlay: str) -> None:
    result = subprocess.run(
        ["kubectl", "kustomize", f"deploy/kubernetes/overlays/{overlay}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "kind: Namespace" in result.stdout
    assert f"bitcoin-bastion-{overlay}" in result.stdout
