from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import reflex as rx

from bastion_ui.routes.access import (
    access_checkout_page,
    access_import_page,
    access_lockdown_page,
    access_me_page,
    access_page,
    access_recovery_page,
    access_success_page,
)
from bastion_ui.routes.check import check_page
from bastion_ui.routes.developers import developers_page
from bastion_ui.routes.docs import docs_page
from bastion_ui.routes.evidence import evidence_page
from bastion_ui.routes.home import home_page
from bastion_ui.routes.manifesto import manifesto_page
from bastion_ui.routes.operations import operations_page
from bastion_ui.routes.platform import platform_page
from bastion_ui.routes.roadmap import roadmap_page
from bastion_ui.routes.security import security_page
from bastion_ui.routes.status import status_page
from bastion_ui.routes.trace import trace_page


@dataclass(frozen=True)
class PublicRouteSpec:
    route: str
    title: str
    page: Callable[[], rx.Component]


PUBLIC_ROUTE_SPECS: tuple[PublicRouteSpec, ...] = (
    PublicRouteSpec("/", "Bitcoin Bastion", home_page),
    PublicRouteSpec("/platform", "Platform", platform_page),
    PublicRouteSpec("/access", "Bastion Access", access_page),
    PublicRouteSpec("/access/checkout", "Access Checkout", access_checkout_page),
    PublicRouteSpec("/access/success", "Access Success", access_success_page),
    PublicRouteSpec("/access/import", "Import Access Pass", access_import_page),
    PublicRouteSpec("/access/me", "Access Status", access_me_page),
    PublicRouteSpec("/access/recovery", "Access Recovery", access_recovery_page),
    PublicRouteSpec("/access/lockdown", "Emergency Lockdown", access_lockdown_page),
    PublicRouteSpec("/check", "Check Bitcoin Address", check_page),
    PublicRouteSpec("/trace", "Bastion Trace", trace_page),
    PublicRouteSpec("/developers", "Developers", developers_page),
    PublicRouteSpec("/operations", "Operations", operations_page),
    PublicRouteSpec("/manifesto", "Manifesto", manifesto_page),
    PublicRouteSpec("/evidence", "Evidence", evidence_page),
    PublicRouteSpec("/status", "Status", status_page),
    PublicRouteSpec("/roadmap", "Roadmap", roadmap_page),
    PublicRouteSpec("/security", "Security", security_page),
    PublicRouteSpec("/docs", "Docs", docs_page),
)
