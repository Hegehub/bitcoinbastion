from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROFILE_DIR = ROOT / "deploy" / "runtime-profiles"

REQUIRED = [
    "README.md",
    "profiles.yaml",
    "compose.yaml",
    "k8s.yaml",
    "k3s.yaml",
    "kind.yaml",
    "minikube.yaml",
    "single-node.yaml",
    "bare-metal-systemd.yaml",
]
PROFILES = ["compose", "k8s", "k3s", "kind", "minikube", "single-node", "bare-metal-systemd"]


def test_runtime_profile_metadata_files_exist() -> None:
    for filename in REQUIRED:
        assert (PROFILE_DIR / filename).exists(), filename


def test_profiles_yaml_lists_supported_profiles() -> None:
    text = (PROFILE_DIR / "profiles.yaml").read_text(encoding="utf-8")
    for profile in PROFILES:
        assert f"- {profile}" in text or f"{profile}:" in text


def test_profiles_yaml_preserves_core_runtime_constraints() -> None:
    text = (PROFILE_DIR / "profiles.yaml").read_text(encoding="utf-8")
    assert "canonical_kubernetes_path: deploy/kubernetes" in text
    assert "kubernetes_required_for_all_profiles: false" in text
    assert "cloud_provider_required: false" in text
    assert "custody_allowed: false" in text
    assert "seed_phrase_handling_allowed: false" in text
    assert "private_key_handling_allowed: false" in text

REQUIRED_FIELDS = [
    "name",
    "runtime_type",
    "status",
    "best_for",
    "recommended_envs",
    "min_cpu",
    "min_ram",
    "ha_supported",
    "evidence_supported",
    "k8s_required",
    "production_suitability",
    "resource_footprint",
    "operational_complexity",
    "operational_risk",
    "requires_cloud_provider",
    "supports_air_gapped",
    "supports_local_only",
    "canonical_paths",
    "commands",
    "limitations",
    "security_notes",
    "evidence_notes",
]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_each_profile_metadata_has_required_fields() -> None:
    for profile in PROFILES:
        metadata = read_text(f"deploy/runtime-profiles/{profile}.yaml")
        for field in REQUIRED_FIELDS:
            assert f"{field}:" in metadata


def test_runtime_profile_docs_are_truthful() -> None:
    docs = read_text("docs/RUNTIME_PROFILES.md").lower()
    assert "kubernetes is supported" in docs
    assert "kubernetes is not mandatory" in docs
    assert "no-custody" in docs
    assert "k3s is the recommended" in docs
    assert "sovereign small deployments" in docs
    assert "kind" in docs and "not production" in docs
    assert "minikube" in docs and "not production" in docs
    assert "all profiles are production-equal" not in docs
    assert "production readiness requires environment evidence artifacts" in docs


def test_canonical_kubernetes_path_is_documented() -> None:
    runtime_docs = read_text("docs/RUNTIME_PROFILES.md")
    profile_readme = read_text("deploy/runtime-profiles/README.md")
    kubernetes_readme = read_text("deploy/kubernetes/README.md")
    for content in (runtime_docs, profile_readme, kubernetes_readme):
        assert "deploy/kubernetes" in content
        assert "canonical" in content.lower()
