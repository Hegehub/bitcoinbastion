# Reflex Frontend Structure

This document defines the canonical file-organization contract for the Bitcoin Bastion Reflex frontend after the naming/structure reorganization.

## Canonical root

`reflex_frontend/` is the primary Reflex frontend root.

The legacy Next.js `frontend/` directory is not restored, expanded, or treated as the primary frontend by this structure. It remains a rollback/archive surface only where still present.

## Application bootstrap

`reflex_frontend/bastion_ui/app.py` is intentionally thin:

- creates the Reflex `rx.App` instance;
- loads the canonical theme from `bastion_ui.theme`;
- delegates all page registration to `bastion_ui.routes.registry`;
- keeps static route markers for existing route-contract tests.

It must not become a catch-all module for route imports, component previews, service clients, or state logic.

## Route ownership

Route declarations live in `reflex_frontend/bastion_ui/routes/registry.py`.

The registry groups routes by domain:

| Group | Constant | Purpose |
|---|---|---|
| Public | `PUBLIC_ROUTE_SPECS` | Static public pages such as `/`, `/platform`, `/status`, `/docs`, `/check`, and `/trace`. |
| Trace | `TRACE_ROUTE_SPECS` | Dynamic Trace routes using `[report_id]`, not `[reportId]`. |
| Console | `CONSOLE_ROUTE_SPECS` | Operator console modules under `/console/*`. |
| Market | `MARKET_ROUTE_SPECS` | Reflex Market routes. FastAPI/Jinja Market routes remain active for delegated/detail views until parity is complete. |
| Development | `DEVELOPMENT_ROUTE_SPECS` | Preview-only routes such as `/design-system`. |

Compatibility constants remain available for tests and route-parity checks:

- `PUBLIC_ROUTES`
- `CONSOLE_ROUTES`
- `MARKET_ROUTES`
- `DEVELOPMENT_ROUTES`
- `ALL_REFLEX_ROUTES`
- `STALE_ROUTES`

## Directory naming contract

The Reflex frontend uses these package boundaries:

| Directory | Responsibility |
|---|---|
| `bastion_ui/routes/` | Route/page functions and route registry only. |
| `bastion_ui/components/` | Reusable UI components, grouped by domain or UI primitive. |
| `bastion_ui/services/` | API clients, DTO mapping, backend integration helpers. |
| `bastion_ui/state/` | Reflex state classes and view state. |
| `bastion_ui/theme/` | Theme construction and visual tokens. |
| `bastion_ui/security/` | Frontend validation, safe-input guards, and route parameter validation. |
| `bastion_ui/copy/` | Copy/i18n constants and safety wording shared by UI modules. |
| `bastion_ui/tests/` | Reflex route, safety, parity, and UI contract tests. |

## Safety constraints

The reorganization must preserve Bitcoin Bastion safety boundaries:

- no custody;
- no seed phrase, private-key, wallet-file, or signing-material collection;
- no trading execution or financial-advice claim;
- Trace remains advisory/application-level analysis;
- Market Intelligence remains historical/informational context;
- delegated FastAPI/Jinja Market routes remain valid until parity is complete.

## Current implementation notes

This structure moves page registration out of `app.py` and into the route registry, extracts the design-system preview into `routes/design_system.py`, centralizes the Reflex theme in `theme/app_theme.py`, and creates the `copy/` package for shared safety/i18n text.
