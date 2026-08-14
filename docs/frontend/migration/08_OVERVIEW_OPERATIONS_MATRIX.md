# Prompt 8 Overview and Operations Matrix

## Feature ownership

The canonical feature register assigns no numbered Feature ID specifically to
Prompt 8. This stage owns the named Overview, Health, Providers and Storage
screens without inventing an ID. Prompt 9 retains Incidents, SLOs, Jobs and
Market overview/signals.

## Authoritative data ownership

| Matrix | Operation | Contract | Adapter / safe model | State | Consumers | Security | Coverage |
|---|---|---|---|---|---|---|---|
| HTTP-0076 | `health_api_v1_health_get` | `HealthOut` | `adapt_health` / `HealthViewModel` | `HealthState` | Overview, Operations, Health | public | IMPLEMENTED_VERIFIED |
| HTTP-0080 | `providers_api_v1_health_providers_get` | `list[ProviderHealthSnapshotOut]` | `adapt_providers` / `ProvidersViewModel` | `ProvidersState` | Overview, Operations, Providers | public | IMPLEMENTED_VERIFIED |
| HTTP-0260 | `storage_status_api_v1_storage_status_get` | `StorageStatusResponse` | `adapt_storage` / `StorageViewModel` | `StorageState` | Overview, Operations, Storage | public | IMPLEMENTED_VERIFIED |

Jobs, degraded-component history, Runtime/System Health and Market provider
operations are FUTURE for Prompt 9 or later and are not fetched here. No
Prompt-8 route consumes a WebSocket; current authoritative HTTP observations
are valid LIVE data.

## DTO → DOM lineage

| Screen | Operation → generated field | Projection → State | Named DOM |
|---|---|---|---|
| Overview / Health | HTTP-0076 → `HealthOut.app/status/details` | `adapt_health` → `HealthViewModel` → `HealthState.value` | `health-application`, `health-status`, labelled detail rows |
| Providers | HTTP-0080 → `provider_name/provider_type/health_state/avg_latency_ms/last_success_at` | `adapt_providers` → `ProviderViewModel` → `ProvidersState.value.providers` | `Providers` list; Name, Type, State, Latency, Last success |
| Storage | HTTP-0260 → `status/profile/summary/stores/degraded_mode` | `adapt_storage` → safe allowlisted `StorageViewModel` → `StorageState.value` | `storage-status`, `storage-profile`, `Storage systems` list |

The storage adapter deliberately drops every `StorageStoreStatus.details`
entry. Connection URLs, credentials, driver metadata and filesystem paths can
therefore never enter Reflex State or DOM through this projection. `None`
latency/capacity stays unknown and is never converted to zero.

## Screen coverage

| Route ID | Path | HTTP dependencies | Trigger | Lifecycle / provenance | Coverage |
|---|---|---|---|---|---|
| `overview.home` | `/` | HTTP-0076/0080/0260 | route entry plus section refresh | independent loading/empty/unavailable/error and LIVE section badges | IMPLEMENTED_VERIFIED |
| `operations` | `/operations` | HTTP-0076/0080/0260 | route entry plus section refresh | independent sections | IMPLEMENTED_VERIFIED |
| `operations.health` | `/operations/health` | HTTP-0076 | route entry / refresh | safe typed errors; Feature-52 section provenance | IMPLEMENTED_VERIFIED |
| `operations.providers` | `/operations/providers` | HTTP-0080 | route entry / refresh | empty distinct from unavailable | IMPLEMENTED_VERIFIED |
| `operations.storage` | `/operations/storage` | HTTP-0260 | route entry / refresh | unknown/degraded preserved; secret fields excluded | IMPLEMENTED_VERIFIED |

All routes use `frontend.core`, public security metadata, canonical
breadcrumbs, command generation and Prompt-7 shell ownership. Request
generations make refresh latest-wins and route exit invalidates all Prompt-8
owners. No fixture is a production fallback.

## Rollback

Independently remove the three detail route records/pages, then the Overview
consumers, State and adapters. Retain generated contracts, Prompt-5 topology,
Feature 52/54, Feature 67, Prompt-6 tokens, Prompt-7 shell and all backend/user
data. Never replace the safe storage projection with raw `details` during
rollback.
