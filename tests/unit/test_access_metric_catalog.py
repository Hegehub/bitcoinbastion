from __future__ import annotations

from app.domain.access.plans import PlanCode
from app.services.access.metric_catalog import (
    get_metric_definition,
    get_metric_group,
    get_metric_group_for_metric,
    list_available_metric_groups,
    list_locked_metric_groups,
    list_metric_groups,
    list_metrics_for_group,
)


def test_metric_catalog_contains_required_groups_and_metrics() -> None:
    groups = {group.code: group for group in list_metric_groups()}

    assert len(groups) == 16
    assert "market.basic" in groups
    assert "btc.price" in {metric.name for metric in groups["market.basic"].metrics}
    assert "trace.advanced.proof_packet" in {metric.name for metric in groups["trace.advanced"].metrics}


def test_metric_lookup_helpers_return_expected_definitions() -> None:
    definition = get_metric_definition("btc.price")

    assert definition is not None
    assert definition.group_code == "market.basic"
    assert get_metric_group_for_metric("btc.price") == "market.basic"
    assert get_metric_group("missing.group") is None
    assert list_metrics_for_group("missing.group") == []


def test_locked_and_available_metric_groups_are_plan_specific() -> None:
    lite_available = list_available_metric_groups(PlanCode.LITE)
    lite_locked = {locked.group_code: locked.required_plan for locked in list_locked_metric_groups(PlanCode.LITE)}

    assert "market.basic" in lite_available
    assert "market.intelligence" in lite_locked
    assert lite_locked["market.intelligence"] is PlanCode.PLUS
    assert "enterprise.custom" in lite_locked


def test_catalog_has_no_broad_all_access_scopes() -> None:
    forbidden = {"metrics:all", "api:all", "admin:all"}
    scopes = {scope for group in list_metric_groups() for scope in group.scopes}

    assert scopes.isdisjoint(forbidden)
