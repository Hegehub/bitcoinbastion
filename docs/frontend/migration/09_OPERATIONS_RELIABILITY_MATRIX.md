# Prompt 9 — Operations reliability authority matrix

## Authority design

| Capability | Existing source | New canonical owner | Persistence | API |
|---|---|---|---|---|
| Incident observations | Typed runtime provider/job/component health | `OperationsIncidentService` detector `runtime-component-availability-v1` | `operations_incidents` | `operations_list_incidents` |
| Incident identity/correlation | Detector + kind + stable target | UUID incident ID; unique nullable active correlation key | durable relational rows | list/detail |
| Incident lifecycle/history | Detector qualifying/clear observations | backend `OPEN`/`RESOLVED`; append-only transitions | `operations_incident_transitions` | incident detail |
| Incident severity | Explicit detector mapping | backend `MAJOR`/`CRITICAL` policy | incident and transition rows | typed enum |
| Operations SLO policy | typed application configuration | `OperationsSLOPolicy` | restart-stable operator configuration | `operations_list_slo` |
| Operations SLI | completed/failed `JobRun` counts | `operations.job_success_ratio` registry owner | canonical job-run store | typed current evaluation |
| Operations SLO evaluation | Decimal measurement + explicit comparator/window | `OperationsSLOService` | read-only deterministic evaluation | typed status/unit/window |

`RecoverySLOOut` remains recovery-owned and is neither imported nor adapted by the Operations UI. Operations SLO supports zero configured policies. Missing samples become `INSUFFICIENT_DATA`; they do not pass or breach.

## Detector policy

| Detector | Source field | Qualifying condition | Clear condition | Kind | Severity |
|---|---|---|---|---|---|
| `runtime-component-availability-v1` | `RuntimeStatusOut.degraded_components[].severity` | `degraded`, `critical`, or `offline` | correlation key absent after a complete typed runtime evaluation | `COMPONENT_AVAILABILITY` | `degraded` → `MAJOR`; `critical`/`offline` → `CRITICAL` |

Repeated qualifying observations update the open incident. A clear observation resolves it. A later recurrence creates a new UUID. The unique active correlation key prevents concurrent duplicate openings.

## Authority-to-DOM lineage

| Surface | Lineage | Named DOM content | Coverage |
|---|---|---|---|
| Incidents | runtime status → detector → incident/history tables → `operations_list_incidents` → generated `IncidentOut` → `adapt_incidents` → `IncidentsViewModel` → `IncidentsState` → `incidents_section` | summary, severity, status, affected target, opened/updated time, source | `IMPLEMENTED_UNVERIFIED` |
| SLO | typed config + job-run telemetry → typed SLI → backend Decimal evaluator → `operations_list_slo` → generated `OperationsSLOOut` → `adapt_operations_slo` → `OperationsSLOViewModel` → `OperationsSLOState` → `slo_section` | title, backend status, target/current/unit, window, samples, observed time | `IMPLEMENTED_UNVERIFIED` |

## Semantic ownership

- Frontend incident severity/status inference count: **0**.
- Frontend SLO policy evaluations: **0**.
- SLO target, comparator, window, data sufficiency and compliance are backend-owned.
- Error-budget and burn-rate fields remain absent (`None`) because no separately justified evaluator is implemented.
- Incident replay means reconstruction from persisted append-only transitions, not infrastructure time travel.
- Jobs, Market Overview, and Market Signals retain their existing repository implementations; this corrective slice does not claim new browser verification for them.

## Security, flags, and lifecycle

Both routes are protected through canonical `access.me` / Feature-67 shell posture, use the core Feature-58 flag, declare their generated operation dependencies, and participate in route-owned request generation invalidation. No page-local HTTP client or WebSocket owner was introduced.

## Rollback

The incident migration/model/service/API, SLO evaluator/API, generated Stage-1 artifacts, adapters/State/screens/routes, and this matrix can be reverted independently. Rollback must retain Recovery SLO separation, Prompt-5 route identifiers that remain referenced, Feature-52's four provenance values, and must not replace unavailable data with fixtures.
