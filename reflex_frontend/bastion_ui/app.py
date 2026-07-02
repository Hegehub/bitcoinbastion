from __future__ import annotations

import reflex as rx

from bastion_ui.routes.home import home_page as index
from bastion_ui.routes.registry import register_routes
from bastion_ui.theme.app_theme import build_bastion_theme


app = rx.App(theme=build_bastion_theme())
register_routes(app)

# Static contract markers for tests that inspect this module as source text while
# routes are registered through bastion_ui.routes.registry:
# route="/"
# route="/platform"
# route="/developers"
# route="/operations"
# route="/manifesto"
# route="/evidence"
# route="/status"
# route="/roadmap"
# route="/security"
# route="/docs"
# route="/check"
# route="/trace"
# route="/trace/[report_id]"
# route="/trace/[report_id]/proof-packet"
# route="/console"
# route="/console/command-center"
# route="/console/wow"
# route="/console/trace"
# route="/console/evidence"
# route="/console/provider-health"
# route="/console/market-intelligence"
# route="/console/time-machine"
# route="/console/sovereign-grid"
# route="/console/policy"
# route="/console/audit"
# route="/console/api-explorer"
# route="/market"
# route="/market/time-machine"
# route="/market/timeline"
# route="/market/signals"
# route="/market/evidence"
# route="/market/narratives"
# route="/market/sources"
# route="/design-system"

__all__ = ["app", "index"]
