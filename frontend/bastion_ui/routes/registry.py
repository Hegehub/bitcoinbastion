from __future__ import annotations

PUBLIC_ROUTES: tuple[str, ...] = (
    "/",
    "/platform",
    "/access",
    "/access/checkout",
    "/access/success",
    "/access/import",
    "/access/me",
    "/access/recovery",
    "/access/lockdown",
    "/developers",
    "/operations",
    "/manifesto",
    "/evidence",
    "/status",
    "/roadmap",
    "/security",
    "/docs",
    "/check",
    "/trace",
    "/trace/[report_id]",
    "/trace/[report_id]/proof-packet",
)

CONSOLE_ROUTES: tuple[str, ...] = (
    "/console",
    "/console/trace",
    "/console/evidence",
    "/console/provider-health",
    "/console/market-intelligence",
    "/console/time-machine",
    "/console/sovereign-grid",
    "/console/policy",
    "/console/audit",
    "/console/api-explorer",
    "/console/wow",
)

MARKET_ROUTES: dict[str, dict[str, str]] = {
    "/market": {"owner": "reflex", "status": "implemented"},
    "/market/timeline": {"owner": "reflex", "status": "implemented"},
    "/market/time-machine": {"owner": "reflex", "status": "implemented"},
    "/market/signals": {"owner": "reflex", "status": "implemented"},
    "/market/evidence": {"owner": "reflex", "status": "implemented"},
    "/market/narratives": {"owner": "reflex", "status": "implemented"},
    "/market/sources": {"owner": "reflex", "status": "implemented"},
}

STALE_ROUTES: frozenset[str] = frozenset({"/products", "/self-host"})
ALL_REFLEX_ROUTES: tuple[str, ...] = PUBLIC_ROUTES + CONSOLE_ROUTES + tuple(MARKET_ROUTES)
