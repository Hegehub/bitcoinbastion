from datetime import UTC, datetime

_ALERTS: list[dict[str, object]] = []


def create_alert(alert_type: str, severity: str, message: str) -> dict[str, object]:
    item = {
        "id": len(_ALERTS) + 1,
        "alert_type": alert_type,
        "severity": severity,
        "status": "OPEN",
        "message": message,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _ALERTS.append(item)
    return item


def list_alerts() -> list[dict[str, object]]:
    return list(_ALERTS)
