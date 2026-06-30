from app.domain.access.decisions import AccessDecision, PolicyDecision
from app.domain.access.entitlements import (
    get_plan_metric_groups,
    get_plan_scopes,
    plan_allows_scope,
    required_plan_for_metric_group,
    required_plan_for_scope,
)
from app.domain.access.errors import InvalidPlanCodeError
from app.domain.access.metrics import METRIC_GROUPS
from app.domain.access.plans import PlanCode, normalize_plan_code, plan_rank
from app.domain.access.scopes import ACCESS_SCOPES, FORBIDDEN_SCOPES


def test_plan_codes_exist_and_are_stable() -> None:
    assert {plan.value for plan in PlanCode} == {
        "lite_pass",
        "basic_pass",
        "plus_pass",
        "pro_pass",
        "business_pass",
        "enterprise_pass",
    }


def test_plan_rank_ordering_is_correct() -> None:
    assert [plan_rank(plan) for plan in PlanCode] == [1, 2, 3, 4, 5, 6]
    assert plan_rank(PlanCode.LITE) < plan_rank(PlanCode.BASIC) < plan_rank(PlanCode.PLUS)
    assert plan_rank(PlanCode.PRO) < plan_rank(PlanCode.BUSINESS) < plan_rank(PlanCode.ENTERPRISE)


def test_normalize_plan_code_rejects_invalid_values() -> None:
    assert normalize_plan_code("pro_pass") is PlanCode.PRO
    try:
        normalize_plan_code("Pro")
    except InvalidPlanCodeError as exc:
        assert "Invalid access plan code" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("invalid plan code was accepted")


def test_scope_and_metric_constants_have_expected_counts() -> None:
    assert len(ACCESS_SCOPES) == 50
    assert len(METRIC_GROUPS) == 24


def test_forbidden_scopes_are_not_present_in_default_mappings() -> None:
    for plan in PlanCode:
        scopes = get_plan_scopes(plan)
        assert not (scopes & FORBIDDEN_SCOPES)
        assert "api:all" not in scopes
        assert "metrics:all" not in scopes
        assert "admin:all" not in scopes
        assert "*" not in scopes


def test_plan_scope_inheritance() -> None:
    assert get_plan_scopes(PlanCode.LITE) <= get_plan_scopes(PlanCode.BASIC)
    assert get_plan_scopes(PlanCode.BASIC) <= get_plan_scopes(PlanCode.PLUS)
    assert get_plan_scopes(PlanCode.PLUS) <= get_plan_scopes(PlanCode.PRO)
    assert get_plan_scopes(PlanCode.PRO) <= get_plan_scopes(PlanCode.BUSINESS)
    assert get_plan_scopes(PlanCode.BUSINESS) <= get_plan_scopes(PlanCode.ENTERPRISE)


def test_plan_metric_inheritance() -> None:
    assert get_plan_metric_groups(PlanCode.LITE) <= get_plan_metric_groups(PlanCode.BASIC)
    assert get_plan_metric_groups(PlanCode.BASIC) <= get_plan_metric_groups(PlanCode.PLUS)
    assert get_plan_metric_groups(PlanCode.PLUS) <= get_plan_metric_groups(PlanCode.PRO)
    assert get_plan_metric_groups(PlanCode.PRO) <= get_plan_metric_groups(PlanCode.BUSINESS)
    assert get_plan_metric_groups(PlanCode.BUSINESS) <= get_plan_metric_groups(PlanCode.ENTERPRISE)


def test_access_checks_by_plan() -> None:
    assert not plan_allows_scope(PlanCode.LITE, "signals:advanced:read")
    assert not plan_allows_scope(PlanCode.LITE, "trace:advanced:read")
    assert not plan_allows_scope(PlanCode.PLUS, "treasury:read")
    assert plan_allows_scope(PlanCode.PRO, "treasury:read")
    assert plan_allows_scope(PlanCode.BUSINESS, "payregister:metrics:read")
    assert plan_allows_scope(PlanCode.ENTERPRISE, "enterprise:policy:custom")


def test_required_plan_checks() -> None:
    assert required_plan_for_scope("trace:advanced:read") is PlanCode.PRO
    assert required_plan_for_scope("payregister:metrics:read") is PlanCode.BUSINESS
    assert required_plan_for_scope("enterprise:policy:custom") is PlanCode.ENTERPRISE
    assert required_plan_for_metric_group("signals.advanced") is PlanCode.PRO
    assert required_plan_for_metric_group("payregister.metrics") is PlanCode.BUSINESS


def test_access_decision_upgrade_required() -> None:
    decision = AccessDecision(
        decision=PolicyDecision.UPGRADE_REQUIRED,
        reason="Plan upgrade required",
        required_plan=PlanCode.PRO,
        current_plan=PlanCode.PLUS,
        requested_scope="treasury:read",
        upgrade_available=True,
    )

    assert decision.decision is PolicyDecision.UPGRADE_REQUIRED
    assert decision.required_plan is PlanCode.PRO
    assert decision.current_plan is PlanCode.PLUS
    assert decision.upgrade_available is True


def test_access_decision_metric_not_allowed() -> None:
    decision = AccessDecision(
        decision=PolicyDecision.METRIC_NOT_ALLOWED,
        reason="Metric group is not allowed for this plan",
        current_plan=PlanCode.BASIC,
        requested_metric_group="signals.advanced",
    )

    assert decision.decision is PolicyDecision.METRIC_NOT_ALLOWED
    assert decision.requested_metric_group == "signals.advanced"


def test_access_decision_deny_does_not_need_to_leak_secrets() -> None:
    decision = AccessDecision(decision=PolicyDecision.DENY, reason="Access denied")

    assert decision.decision is PolicyDecision.DENY
    assert "secret" not in decision.reason.lower()
    assert "token" not in decision.reason.lower()
    assert "pass" not in decision.reason.lower()
