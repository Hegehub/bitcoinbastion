from bastion_ui.components.console.console_nav import CONSOLE_NAV_ITEMS


def test_console_navigation_contains_all_modules() -> None:
    expected = {
        "Dashboard": "/console",
        "Trace": "/console/trace",
        "Evidence": "/console/evidence",
        "Provider Health": "/console/provider-health",
        "Market Intelligence": "/console/market-intelligence",
        "Time Machine": "/console/time-machine",
        "Sovereign Grid": "/console/sovereign-grid",
        "Policy Engine": "/console/policy",
        "Audit Log": "/console/audit",
        "Deployment Status": "/console/deployment",
        "API Explorer": "/console/api-explorer",
    }
    assert dict(CONSOLE_NAV_ITEMS) == expected
