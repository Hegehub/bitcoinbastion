# Prompt 5 Route, Navigation and Feature-Flag Matrix

## P5R2 gap closure

| Gap | Original symbol | Closure | Evidence |
|---|---|---|---|
| route consumers | literal `href` values in layout/domain components | `path_for` or `dynamic_route_parts`; AST validator rejects new literal internal hrefs | `test_internal_literal_href_validator_is_clean` |
| flag enforcement | `FLAGS` metadata only | application registration and navigation both consume one resolved flag map | `test_disabled_direct_url_and_navigation_are_enforced` |
| disabled route | no direct-URL gate | canonical `feature_disabled_page` wrapper, distinct copy and no fixture fallback | Prompt-5 component/browser tests |
| dependencies | unvalidated route tuples | HTTP ownership, WS family, security, flag and product validation | `validate_dependencies` |
| aliases/redirects | stale paths only | typed aliases and registered internal-only redirects | alias/open-redirect tests |
| lifecycle | no router coordinator | route on-load coordinates existing HTTP generation, Feature-67 invalidation and Stage-4 disconnect/connect owners | transition and WS transport tests |
| not found | framework fallback | last-registered Reflex optional catch-all renders semantic recovery surface | export/browser 404 test |
| malformed detail | route accepted arbitrary segment | conservative dynamic matching plus route-state validation before content | malformed-route tests |

The executable source of truth is `bastion_ui.topology.ROUTES`. Paths are
resolved from stable route IDs; desktop and mobile navigation filter the same
registry. Route registration is structural coverage only and does not promote a
screen beyond its existing coverage state.

## Information architecture

Bitcoin Bastion Core contains Overview, Operations, Market, Trace, Evidence,
Access, Console and LNURL domains. PayRegister is a separate product and is OFF
by default. Protocol, transient detail and development routes are not ordinary
navigation items. Prompt 7 classifies legacy `/console/wow` as a deprecated,
internal-only alias to Command Center; it accepts no destination parameter and
cannot become an open redirect or separate route owner.

## Route fields and validation

Each record declares stable ID, canonical path, product/domain, component,
title, route class, Feature-67 requirement reference, typed flag, navigation
placement, breadcrumb parent, availability policy, HTTP/WS dependencies and
future implementation prompt. Validation rejects duplicate IDs or paths,
malformed dynamic parameters, unknown parents/components and product-boundary
violations. Dynamic values use a conservative allowlist and URL encoding.

## Navigation semantics

`HIDDEN`, `DISABLED`, `DENIED`, and `UNAVAILABLE` are separate outcomes:

* hidden means the registered route is inappropriate in current navigation;
* disabled means its typed rollout flag is OFF;
* denied is a Feature-67/backend-authoritative security result;
* unavailable is a request/WebSocket lifecycle result.

Flags and navigation never authorize. Backend denial wins. Fixtures never
convert unavailable service data to LIVE.

## Flag matrix

| Flag | Owner | Default | Production | Rollback | Removal |
|---|---|---|---|---|---|
| `frontend.core` | Frontend/Core | ON | allowed | stop route lifecycle, retain recovery | permanent |
| `frontend.console` | Frontend/Console | LIMITED | allowed | remove nav and release HTTP/WS work | console acceptance |
| `frontend.payregister` | PayRegister | OFF | allowed | remove separate-product nav, preserve merchant data | product launch decision |
| `frontend.websocket_lab` | Feature 59 | INTERNAL | forced OFF | close canonical subscription and suppress reconnect | lab retirement |
| `frontend.design_system` | Frontend development | INTERNAL | forced OFF | hide development route | preview retirement |

Resolution precedence is deterministic: typed default, then trusted process
environment (`BASTION_FLAG_<ENUM_NAME>`), then production isolation. Query
parameters, browser storage, cookies, random cohorts and mutable browser State
are not sources. Unknown IDs and invalid values fail validation.

## Reversible rollback

Revert Prompt-5 registry consumers as one unit while retaining canonical
Stage-1 contracts, Stage-2 lifecycle/provenance, Feature 67, and Stage-4 socket
ownership. Individual high-risk surfaces are disabled through their typed flag;
disable handlers must cancel route-owned requests/subscriptions through the
existing lifecycle managers. Rollback never changes Access posture, deletes
user data, or restores duplicate/insecure route ownership.
