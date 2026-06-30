import json
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from app.core.telemetry import OBSERVABILITY_METRIC_NAMES, bounded_label
from app.main import app


def test_root_health_endpoints_task46() -> None:
    client = TestClient(app)
    for path in [
        "/health/live",
        "/health/ready",
        "/health/startup",
        "/health/dependencies",
        "/health/providers",
        "/health/intelligence",
        "/health/operations",
    ]:
        response = client.get(path)
        assert response.status_code == 200


def test_operations_api_contracts_task46() -> None:
    client = TestClient(app)
    for path in [
        "/api/v1/operations/status",
        "/api/v1/operations/providers",
        "/api/v1/operations/drills",
        "/api/v1/operations/metrics-summary",
        "/api/v1/operations/runbooks",
    ]:
        response = client.get(path)
        assert response.status_code == 200
    payload = client.get("/api/v1/operations/status").json()
    assert {
        "platform_status",
        "dependency_status",
        "provider_status",
        "operations_timeline",
        "recovery_drills",
        "system_health",
        "alert_summary",
    }.issubset(payload)


def test_bastion_metrics_registration_and_bounded_endpoint_labels_task46() -> None:
    required = {
        "bastion_http_requests_total",
        "bastion_http_request_duration_seconds",
        "bastion_news_fetch_total",
        "bastion_provider_health_score",
        "bastion_background_job_failures_total",
        "bastion_provider_degraded_total",
    }
    assert required.issubset(set(OBSERVABILITY_METRIC_NAMES))
    assert bounded_label("endpoint", "/article/free-text") == "unknown"
    assert bounded_label("endpoint", "operations_status") == "operations_status"


def test_alert_rules_and_dashboards_task46() -> None:
    rules = yaml.safe_load(
        Path("deploy/kubernetes/observability/prometheus-rules-operations.yaml").read_text()
    )
    alerts = {rule["alert"] for group in rules["spec"]["groups"] for rule in group["rules"]}
    assert "BitcoinBastionDatabaseUnavailable" in alerts
    assert "BitcoinBastionEvidenceIntegrityFailures" in alerts
    for dashboard in [
        "grafana-dashboard-platform-overview.json",
        "grafana-dashboard-intelligence.json",
        "grafana-dashboard-provider.json",
        "grafana-dashboard-evidence.json",
        "grafana-dashboard-operator.json",
    ]:
        data = json.loads(Path("deploy/kubernetes/observability", dashboard).read_text())
        assert data["title"].startswith("Bitcoin Bastion")
        assert data["panels"]


def test_operations_cronjob_generation_and_gitops_inclusion_task46() -> None:
    cronjob_text = Path("deploy/kubernetes/base/operations-cronjobs.yaml").read_text()
    for name in [
        "bitcoin-bastion-news-fetch",
        "bitcoin-bastion-btc-collection",
        "bitcoin-bastion-candle-generation",
        "bitcoin-bastion-impact-calculation",
        "bitcoin-bastion-attribution-refresh",
        "bitcoin-bastion-source-reputation-refresh",
        "bitcoin-bastion-news-shock-refresh",
        "bitcoin-bastion-cleanup",
        "bitcoin-bastion-integrity-verification",
    ]:
        assert name in cronjob_text
    assert (
        "operations-cronjobs.yaml" in Path("deploy/kubernetes/base/kustomization.yaml").read_text()
    )
    assert "/health/startup" in Path("deploy/kubernetes/base/api-deployment.yaml").read_text()


def test_runbooks_exist_task46() -> None:
    for runbook in [
        "docs/RUNBOOK_DATABASE.md",
        "docs/RUNBOOK_WORKERS.md",
        "docs/RUNBOOK_PROVIDERS.md",
        "docs/RUNBOOK_TELEGRAM.md",
        "docs/RUNBOOK_DEPLOYMENT.md",
    ]:
        text = Path(runbook).read_text()
        assert "# Runbook" in text
