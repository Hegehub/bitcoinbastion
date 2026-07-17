from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_deployment_assets_have_one_canonical_root() -> None:
    for retired_root in ("argocd", "docker", "helm", "k8s"):
        assert not (ROOT / retired_root).exists(), retired_root

    assert (ROOT / "deploy" / "README.md").exists()
    assert (ROOT / "deploy" / "helm" / "README.md").exists()
    assert (ROOT / "deploy" / "kubernetes" / "README.md").exists()
    assert (ROOT / "deploy" / "kubernetes" / "base" / "kustomization.yaml").exists()
    assert (
        ROOT
        / "deploy"
        / "kubernetes"
        / "overlays"
        / "production"
        / "kustomization.yaml"
    ).exists()
    assert (ROOT / "deploy" / "kubernetes" / "gitops" / "README.md").exists()
    assert (
        ROOT
        / "deploy"
        / "kubernetes"
        / "gitops"
        / "argocd-application-production.yaml"
    ).exists()
    assert (ROOT / "deploy" / "helm" / "bitcoin-bastion" / "Chart.yaml").exists()
    assert (ROOT / "deploy" / "helm" / "bitcoin-bastion" / "values.yaml").exists()


def test_conventional_container_entrypoints_remain_at_repository_root() -> None:
    assert (ROOT / "Dockerfile").is_file()
    assert (ROOT / "docker-compose.yml").is_file()


def test_frontend_has_one_canonical_root() -> None:
    assert not (ROOT / "reflex_frontend").exists()
    assert (ROOT / "frontend").is_dir()
    assert (ROOT / "app" / "bot").is_dir()


def test_frontend_consumers_use_canonical_path() -> None:
    consumers = {
        ".github/workflows/reflex-frontend.yml": "working-directory: frontend",
        "Makefile": "cd frontend",
        "deploy/compose/full-reflex.compose.yaml": "context: ../../frontend",
        "deploy/compose/reflex-frontend.compose.yaml": "context: ../../frontend",
        "scripts/check_frontend_contracts.py": 'read("frontend/bastion_ui/app.py")',
        "scripts/check_route_api_parity.py": 'read("frontend/bastion_ui/app.py")',
    }
    for relative_path, canonical_marker in consumers.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "reflex_frontend" not in text, relative_path
        assert canonical_marker in text, relative_path
