# WebSocket Frontend Matrix

The nine channels are generated in the complete JSON matrix. All currently have **no verified Reflex subscriber** and coverage `NOT_STARTED`.

| Channel family | Message/auth contract | Reconnect and fallback | Owner/prompt |
|---|---|---|---|
| events | broker event plus system/error envelopes; topics validated; auth/origin review unresolved | heartbeat 10–120 s; bounded jittered reconnect; replay request visibly reports unavailable; HTTP fallback | Core, Prompt 5 |
| signals/news/market/intelligence-timeline | specialized event-type filters; payload limiting defaults on | freeze last value as stale, never silently live; matching HTTP read model | Market, Prompt 5 then 16–20 |
| onchain | specialized public operational data only | stale age and HTTP status fallback | Core, Prompt 5/41 |
| trace | public-data advisory events only | report polling fallback; disagreement/partial preserved | Trace, Prompt 5/21–25 |
| treasury | operator capability and Human Intent boundary required; no execution | disconnect disables mutation affordances | Operator Console, Prompt 5/39 |
| provider-health | operator capability; limited payload | provider HTTP health fallback and degraded badge | Operations, Prompt 5/15 |

No channel may transport signing material, one-time credentials, recovery factors or rejected sensitive input. `last_event_id` replay is explicitly unavailable in the current backend.
