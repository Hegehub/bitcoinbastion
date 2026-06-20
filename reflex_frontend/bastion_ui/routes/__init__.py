from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import reflex as rx

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


@dataclass(frozen=True)
class PublicRouteSpec:
    route: str
    title: str
    page: Callable[[], rx.Component]


PUBLIC_ROUTE_SPECS: tuple[PublicRouteSpec, ...] = (
    PublicRouteSpec("/", "Bitcoin Bastion", home_page),
    PublicRouteSpec("/platform", "Platform", platform_page),
    PublicRouteSpec("/developers", "Developers", developers_page),
    PublicRouteSpec("/operations", "Operations", operations_page),
    PublicRouteSpec("/manifesto", "Manifesto", manifesto_page),
    PublicRouteSpec("/evidence", "Evidence", evidence_page),
    PublicRouteSpec("/status", "Status", status_page),
    PublicRouteSpec("/roadmap", "Roadmap", roadmap_page),
    PublicRouteSpec("/security", "Security", security_page),
    PublicRouteSpec("/docs", "Docs", docs_page),
)
