# Operations

Operators should start with `/api/v1/health/runtime` and `/api/v1/health/degraded` during every incident. A degraded state exposes severity, affected component, start time, recommendation and whether an automatic fallback was used.

## Fallback philosophy

The platform can continue API and web operation while providers or Telegram are degraded, but it must not fake a healthy state. Publication failures are logged, background job failures stay visible, and evidence-generation backlogs require operator attention.

## Recovery lifecycle

Recovery tracking follows:

1. failure detected;
2. fallback activated;
3. service restored;
4. recovery confirmed.

Recovery rows store component, failure time, optional fallback activation, recovery time, duration, whether recovery was automatic and whether an operator confirmed it.

## Operations API

Use `/api/v1/operations/status` for the control-plane overview, `/api/v1/operations/drills` for recovery drill evidence, `/api/v1/operations/metrics-summary` for SLO monitoring, and `/api/v1/operations/runbooks` for operator response links.

Recovery drills must store evidence in `operations_evidence` and include drill ID, drill type, timestamps, success, operator, notes, and artifact references.

## Operational health aggregation

`OperationalHealthService` aggregates news providers, price providers, timeline builders, impact, attribution, similarity, evidence, replay, signal, Telegram, web, API and scheduler health. Readiness is degraded unless at least one news provider, one price provider, the timeline engine, database and scheduler are operational.
