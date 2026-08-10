from __future__ import annotations

from dataclasses import dataclass

from bastion_ui.transport.generated_http import GETMEAPIV1ACCESSMEGET_SECURITY


@dataclass(frozen=True)
class RouteSecurityRequirement:
    route: str
    public: bool
    operation_id: str | None
    security_profile: str | None
    required_capability: str | None
    future_owner: str


ROUTE_SECURITY_REQUIREMENTS = {
    "/": RouteSecurityRequirement("/", True, None, None, None, "Public shell"),
    "/access/security-posture": RouteSecurityRequirement(
        "/access/security-posture",
        False,
        "get_me_api_v1_access_me_get",
        GETMEAPIV1ACCESSMEGET_SECURITY.identity,
        None,
        "Prompt 16/25",
    ),
}


def requirement_for(route: str) -> RouteSecurityRequirement:
    requirement = ROUTE_SECURITY_REQUIREMENTS.get(route)
    if requirement is None:
        return RouteSecurityRequirement(route, False, None, None, None, "Unassigned")
    return requirement
