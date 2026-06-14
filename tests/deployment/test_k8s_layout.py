from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
K8S = ROOT / "deploy" / "kubernetes"


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_k8s_overlays_exist_under_canonical_path() -> None:
    for env in ("dev", "staging", "production", "k3s", "single-node", "kind", "minikube"):
        assert (K8S / "overlays" / env / "kustomization.yaml").exists()


def test_kind_and_minikube_overlay_files_exist() -> None:
    for env in ("kind", "minikube"):
        overlay = K8S / "overlays" / env
        assert (overlay / "kustomization.yaml").exists()
        assert (overlay / "namespace.yaml").exists()
        assert (overlay / "patch-env.yaml").exists()
        assert (overlay / "README.md").exists()
    assert (K8S / "overlays" / "kind" / "patch-nodeport.yaml").exists()
    assert (K8S / "overlays" / "minikube" / "patch-ingress.yaml").exists()


def test_local_overlay_namespaces_and_base_references() -> None:
    kind_namespace = read("deploy/kubernetes/overlays/kind/namespace.yaml")
    minikube_namespace = read("deploy/kubernetes/overlays/minikube/namespace.yaml")
    kind_kustomization = read("deploy/kubernetes/overlays/kind/kustomization.yaml")
    minikube_kustomization = read("deploy/kubernetes/overlays/minikube/kustomization.yaml")
    assert "name: bitcoin-bastion-kind" in kind_namespace
    assert "bastion.runtime/profile: kind" in kind_namespace
    assert "name: bitcoin-bastion-minikube" in minikube_namespace
    assert "bastion.runtime/profile: minikube" in minikube_namespace
    assert "../../base" in kind_kustomization
    assert "../../base" in minikube_kustomization


def test_local_overlay_readmes_are_local_only_and_no_custody() -> None:
    kind_readme = read("deploy/kubernetes/overlays/kind/README.md").lower()
    minikube_readme = read("deploy/kubernetes/overlays/minikube/README.md").lower()
    assert "local kubernetes testing only" in kind_readme
    assert "not a production deployment profile" in kind_readme
    assert "does not prove production readiness" in kind_readme
    assert "no-custody" in kind_readme
    assert "seed phrases" in kind_readme
    assert "local minikube testing only" in minikube_readme
    assert "not a production deployment profile" in minikube_readme
    assert "does not prove production readiness" in minikube_readme
    assert "no-custody" in minikube_readme
    assert "seed phrases" in minikube_readme


def test_runtime_profiles_document_kind_and_minikube_truthfully() -> None:
    docs = read("docs/RUNTIME_PROFILES.md").lower()
    assert "kind" in docs
    assert "minikube" in docs
    assert "kind is for local manifest validation and smoke testing" in docs
    assert "minikube is for local operator testing and ingress experiments" in docs
    assert "neither kind nor minikube is production-ready" in docs
    assert "neither profile proves production readiness" in docs
    assert "kind is a production-ready" not in docs
    assert "minikube is a production-ready" not in docs


def test_makefile_has_local_overlay_targets() -> None:
    makefile = read("Makefile")
    assert "runtime-render-kind:" in makefile
    assert "kubectl kustomize deploy/kubernetes/overlays/kind" in makefile
    assert "runtime-render-minikube:" in makefile
    assert "kubectl kustomize deploy/kubernetes/overlays/minikube" in makefile
    assert "deploy-kind:" in makefile
    assert "deploy-minikube:" in makefile
