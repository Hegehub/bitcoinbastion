from __future__ import annotations

STATUS_ROLE = "status"
ALERT_ROLE = "alert"
NAVIGATION_ROLE = "navigation"
MAIN_ROLE = "main"
DIALOG_ROLE = "dialog"
TABLIST_ROLE = "tablist"
TABPANEL_ROLE = "tabpanel"


def aria_label(label: str) -> dict[str, str]:
    return {"aria-label": label}


def described_by(element_id: str) -> dict[str, str]:
    return {"aria-describedby": element_id}
