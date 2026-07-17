from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_env_example_documents_storage_foundation_values() -> None:
    text = _read(".env.example")

    for expected in (
        "OBJECT_STORAGE_ENABLED=true",
        "OBJECT_STORAGE_PROVIDER=minio",
        "OBJECT_STORAGE_ENDPOINT=http://minio:9000",
        "OBJECT_STORAGE_PUBLIC_ENDPOINT=http://localhost:9000",
        "OBJECT_STORAGE_BUCKET=bitcoin-bastion-artifacts",
        "OBJECT_STORAGE_EVIDENCE_RETENTION_DAYS=2555",
        "OBJECT_STORAGE_MAX_ARTIFACT_BYTES=104857600",
        "unsafe defaults",
    ):
        assert expected in text


def test_docker_compose_includes_minio_and_bucket_bootstrap() -> None:
    text = _read("docker-compose.yml")

    assert "minio/minio" in text
    assert "minio-init" in text
    assert "bitcoin-bastion-artifacts" in text
    assert "9000:9000" in text
    assert "9001:9001" in text


def test_kubernetes_base_exposes_non_secret_object_storage_config() -> None:
    text = _read("deploy/kubernetes/base/configmap.yaml")

    for env_name in (
        "OBJECT_STORAGE_ENABLED",
        "OBJECT_STORAGE_PROVIDER",
        "OBJECT_STORAGE_ENDPOINT",
        "OBJECT_STORAGE_BUCKET",
        "OBJECT_STORAGE_REGION",
        "OBJECT_STORAGE_FORCE_PATH_STYLE",
        "OBJECT_STORAGE_EVIDENCE_RETENTION_DAYS",
        "OBJECT_STORAGE_MAX_ARTIFACT_BYTES",
    ):
        assert env_name in text


def test_kubernetes_secret_example_uses_placeholders_not_real_object_storage_secrets() -> None:
    text = _read("deploy/kubernetes/base/secret.example.yaml")

    assert "OBJECT_STORAGE_ACCESS_KEY" in text
    assert "OBJECT_STORAGE_SECRET_KEY" in text
    assert "replace-with-object-storage-access-key" in text
    assert "replace-with-object-storage-secret-key" in text
    assert "minioadmin" not in text


def test_minio_kubernetes_manifest_is_example_only_not_base_resource() -> None:
    manifest = _read("deploy/kubernetes/base/minio.example.yaml")
    kustomization = _read("deploy/kubernetes/base/kustomization.yaml")

    assert "example only" in manifest.lower()
    assert "not recommended as the default production object storage" in manifest.lower()
    assert "PersistentVolumeClaim" in manifest
    assert "minio.example.yaml" not in kustomization


def test_helm_values_contain_external_object_storage_section() -> None:
    text = _read("deploy/helm/bitcoin-bastion/values.yaml")

    assert "objectStorage:" in text
    assert "enabled: false" in text
    assert "provider: s3" in text
    assert "bucket: bitcoin-bastion-artifacts" in text
    assert "existingSecret:" in text
    assert "accessKeySecretKey: OBJECT_STORAGE_ACCESS_KEY" in text
    assert "secretKeySecretKey: OBJECT_STORAGE_SECRET_KEY" in text


def test_runtime_profiles_document_object_storage_expectations() -> None:
    for path in (
        "deploy/runtime-profiles/compose.yaml",
        "deploy/runtime-profiles/single-node.yaml",
        "deploy/runtime-profiles/k8s.yaml",
        "deploy/runtime-profiles/k3s.yaml",
    ):
        text = _read(path)
        assert "storage_foundation:" in text
        assert "object_storage:" in text
        assert "redis: required_ephemeral" in text
