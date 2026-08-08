# Route, Component and Trigger Matrix

## Inventory result

`frontend/bastion_ui/app.py`, navigation, registry, routes, State and services contain registered public, console, compatibility and preview surfaces. Registration alone is not implementation. Source inspection found **zero `on_load=` bindings and zero `rx.foreach` calls**. Async State methods are numerous, but trigger/consumer/render inverse mappings require runtime validation in Prompt 3.

| Route group | Current status | Entry/trigger evidence | Migration/removal gate |
|---|---|---|---|
| `/`, public information routes | active/compatibility mix | registered; request-to-render not comprehensively proven | Overview Prompt 8, named-field browser evidence |
| `/operations` | active | registered; live lifecycle not proven | Operations Prompts 8–9 |
| Market and time-machine routes | active/console compatibility | State/client methods exist; no global on-load binding found | Prompts 9–11, pagination/filter and provenance |
| `/trace`, `/trace/[report_id]` | active | submit handler is confirmed trigger candidate; dynamic binding needs browser proof | Prompts 12–13 |
| Evidence routes | active | State methods exist; trigger/render chain unverified | Prompts 14–15 |
| Access/wallet/LNURL | active/preview | event handlers exist; PoA security and one-time values unverified | Prompts 16–18/22 |
| `/console/*` | operator/preview/compatibility | many refresh methods; invocation and rendering incomplete | Prompts 19–21 |
| `/console/wow` | preview, retained | Wow State/client and placeholder-like cards; no verified lifecycle | extract Prompt 7; remove only after compatibility decision |
| PayRegister | separate product | no core ownership granted | Prompt 22 and feature flag |

## Inverse-mapping rule

For each service and State method, Prompt 1's validator must record: all consumers; explicit event/lifecycle/subscription trigger; named rendered fields; duplicate/unused status; contract test; browser request and DOM assertion. Until then methods remain candidate `CLIENT_ONLY`/`STATE_ONLY`, not implemented. Dynamic route params must be bound and tested; lists require real iteration, pagination/filter/search where contract supports it.
