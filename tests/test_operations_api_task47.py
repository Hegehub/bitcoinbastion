from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from app.main import app


def test_operations_health_readiness_liveness_endpoints_task47() -> None:
    client = TestClient(app)
    for path in [
        "/api/v1/operations/health",
        "/api/v1/operations/jobs",
        "/api/v1/operations/metrics",
        "/api/v1/operations/readiness",
        "/api/v1/operations/liveness",
    ]:
        response = client.get(path)
        assert response.status_code == 200
    payload = client.get("/api/v1/operations/health").json()
    assert {"system_status", "provider_status", "scheduler_status", "timeline_status", "evidence_status", "signal_queue_status", "last_backup", "last_restore_test", "last_integrity_scan"}.issubset(payload)
    assert payload["degraded_state_visible"] is True
    assert payload["operator_visible"] is True


def test_exact_cronjob_registration_task47() -> None:
    text = Path("deploy/kubernetes/base/operations-cronjobs.yaml").read_text()
    for job in [
        "news.fetch",
        "news.score_unprocessed",
        "news.cluster_events",
        "market.collect_btc_price",
        "market.build_candles",
        "market.calculate_price_impact",
        "intelligence.attribute_candles",
        "intelligence.refresh_patterns",
        "intelligence.refresh_similarity",
        "intelligence.update_news_shock_index",
        "signals.create_candidates",
        "signals.publish",
        "evidence.generate_packets",
        "evidence.integrity_scan",
        "operations.health_snapshot",
        "operations.cleanup_expired",
    ]:
        assert f'operations.bitcoinbastion.io/job-name: "{job}"' in text


def test_disaster_recovery_alert_rules_and_runbooks_task47() -> None:
    rules = yaml.safe_load(Path("deploy/kubernetes/observability/prometheus-rules-disaster-recovery.yaml").read_text())
    alerts = {rule["alert"] for group in rules["spec"]["groups"] for rule in group["rules"]}
    assert "BitcoinBastionAllNewsProvidersOffline" in alerts
    assert "BitcoinBastionBackupValidationFailure" in alerts
    assert "BitcoinBastionRestoreValidationFailure" in alerts
    for runbook in [
        "provider_failure.md",
        "timeline_rebuild.md",
        "evidence_integrity.md",
        "signal_queue_recovery.md",
        "telegram_failure.md",
        "database_restore.md",
        "full_disaster_recovery.md",
    ]:
        assert Path("docs/runbooks", runbook).exists()
