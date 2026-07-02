from __future__ import annotations

from pathlib import Path


EXPECTED_PLATFORM_LAYERS = {
    "frontend",
    "backend",
    "database",
    "cache",
    "queue",
    "workers",
    "scheduler",
    "auth",
    "object-storage",
    "search",
    "ci-cd",
    "docker",
    "monitoring",
    "logging",
    "alerts",
    "backup",
    "secrets",
    "security",
    "admin-panel",
    "docs",
    "tests",
    "api-gateway",
    "service-mesh",
    "event-bus",
    "distributed-tracing",
    "observability-stack",
    "audit-logs",
    "rbac-abac",
    "feature-flags",
    "multi-region-infra",
    "disaster-recovery",
    "zero-trust-networking",
    "policy-engine",
    "data-warehouse",
    "ml-analytics-layer",
    "compliance-layer",
    "internal-developer-platform",
}


def test_platform_layer_directories_have_readmes() -> None:
    root = Path(__file__).resolve().parents[2]
    platform_dir = root / "platform"

    assert (platform_dir / "README.md").is_file()
    assert (platform_dir / "layers.yaml").is_file()

    missing = sorted(
        layer for layer in EXPECTED_PLATFORM_LAYERS if not (platform_dir / layer / "README.md").is_file()
    )

    assert missing == []


def test_platform_manifest_mentions_all_layers() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = (root / "platform" / "layers.yaml").read_text(encoding="utf-8")

    missing = sorted(
        layer for layer in EXPECTED_PLATFORM_LAYERS if f"id: {layer}" not in manifest
    )

    assert missing == []
