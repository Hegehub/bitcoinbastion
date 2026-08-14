"""Route-derived, presentation-only shell context."""

from __future__ import annotations

import re
from typing import cast

import reflex as rx

from bastion_ui.navigation import active_route_id
from bastion_ui.topology import ROUTE_BY_ID, breadcrumbs, path_for


def shell_metadata(path: str) -> dict[str, object]:
    """Reconstruct shell context for deep links, refresh, and history navigation."""
    route_id = active_route_id(path) or ""
    route = ROUTE_BY_ID.get(route_id)
    if route is None:
        return {
            "route_id": "",
            "title": "Page not found",
            "context": "Bitcoin Bastion · Unknown route",
            "breadcrumbs": (("Page not found", "", True),),
        }
    pattern = re.escape(route.path)
    for parameter in re.findall(r"\[([^]]+)\]", route.path):
        pattern = pattern.replace(rf"\[{parameter}\]", rf"(?P<{parameter}>[^/]+)")
    match = re.fullmatch(pattern, path)
    parameters = match.groupdict() if match else {}

    def breadcrumb_path(route_id: str) -> str:
        required = re.findall(r"\[([^]]+)\]", ROUTE_BY_ID[route_id].path)
        return path_for(route_id, **{name: parameters[name] for name in required})

    return {
        "route_id": route.id,
        "title": route.title,
        "context": f"{route.product.value} · {route.domain}",
        "breadcrumbs": tuple(
            (item.title, breadcrumb_path(item.id), item.id == route.id)
            for item in breadcrumbs(route.id)
        ),
    }


class ShellState(rx.State):
    """Derived metadata only; domain data and transport ownership stay upstream."""

    @rx.var
    def current_route_id(self) -> str:
        return str(shell_metadata(self.router.url.path)["route_id"])

    @rx.var
    def route_title(self) -> str:
        return str(shell_metadata(self.router.url.path)["title"])

    @rx.var
    def route_context(self) -> str:
        return str(shell_metadata(self.router.url.path)["context"])

    @rx.var
    def breadcrumb_items(self) -> list[dict[str, str]]:
        trail = cast(
            tuple[tuple[str, str, bool], ...], shell_metadata(self.router.url.path)["breadcrumbs"]
        )
        return [
            {"title": title, "path": path, "current": "true" if current else "false"}
            for title, path, current in trail
        ]
