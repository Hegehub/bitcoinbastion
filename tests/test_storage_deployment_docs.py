from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_storage_deployment_doc_mentions_required_surfaces() -> None:
    text = (ROOT / "docs/STORAGE_DEPLOYMENT.md").read_text(encoding="utf-8")

    for required in (
        "docker compose up db redis minio minio-init app worker",
        "deploy/kubernetes/base/",
        "objectStorage:",
        "GET /api/v1/storage/status",
        "Object Storage must never contain",
        "Object Storage down",
    ):
        assert required in text


def test_storage_deployment_doc_lists_required_object_storage_env_vars() -> None:
    text = (ROOT / "docs/STORAGE_DEPLOYMENT.md").read_text(encoding="utf-8")

    for env_name in (
        "OBJECT_STORAGE_ENABLED",
        "OBJECT_STORAGE_PROVIDER",
        "OBJECT_STORAGE_ENDPOINT",
        "OBJECT_STORAGE_PUBLIC_ENDPOINT",
        "OBJECT_STORAGE_BUCKET",
        "OBJECT_STORAGE_REGION",
        "OBJECT_STORAGE_ACCESS_KEY",
        "OBJECT_STORAGE_SECRET_KEY",
        "OBJECT_STORAGE_FORCE_PATH_STYLE",
        "OBJECT_STORAGE_EVIDENCE_RETENTION_DAYS",
        "OBJECT_STORAGE_MAX_ARTIFACT_BYTES",
    ):
        assert env_name in text


def test_storage_deployment_doc_declares_forbidden_sensitive_material() -> None:
    text = (ROOT / "docs/STORAGE_DEPLOYMENT.md").read_text(encoding="utf-8").lower()

    for forbidden in (
        "bitcoin seed phrases",
        "bitcoin private keys",
        "wallet files",
        "xprv",
        "raw access pass bearer tokens",
        "raw api secrets",
        "unredacted sensitive material",
    ):
        assert forbidden in text
