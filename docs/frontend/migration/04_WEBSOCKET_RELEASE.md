# Prompt 4 WebSocket contract and lifecycle release

The backend owns `bitcoin-bastion.events` wire version 1 in `websocket_contracts.py`; version 1 is accepted and every incompatible required-field, discriminator, unit, timestamp, ordering, or enum change requires a new version. Unknown versions and malformed frames fail closed. System, heartbeat, safe error and event frames form one strict discriminated union. The event payload is an explicitly reviewed bounded sanitized JSON-facts map because the durable outbox contract intentionally supports registered heterogeneous event types.

All nine routes are registered in `websocket_registry.py` with B05–B13 identity, security posture, direction, ordering, duplicate/gap policy, visibility policy, buffer bound and exactly one frontend owner. They are server-to-client, public advisory limited-payload streams today; no secret is accepted in a URL. Treasury frames notify only and cannot execute mutations.

The canonical frontend transport validates frames, prevents duplicate connections, suppresses duplicate event IDs in a bounded 128-ID window, and applies capped exponential reconnect delays from 0.5 to 30 seconds for at most five attempts. Unsupported versions and authorization failures are permanent. Route/visibility cleanup disconnects; offline state pauses reconnect. Since replay is unavailable, a gap becomes degraded and requires current HTTP refresh.

Feature 60 provides fixed versioned fixtures that are always `DEMO_FIXTURE`. Feature 59 is an isolated development/test laboratory for malformed and unsupported-version scenarios. Production failure remains `UNAVAILABLE`; fixtures never silently replace live data.

The canonical harness is B12 `/api/v1/ws/provider-health`. The real `connection.accepted` frame maps `stream`, `message`, `topics`, and `wire_version` through `SystemFrame`, `adapt_connection_accepted`, `StreamStatusViewModel`, `WebSocketLabState`, and DOM IDs `ws-stream`, `ws-message`, `ws-version`, and `ws-provenance`.

Headless Chromium observed two real provider-health handshakes and v1 frames (initial plus reconnect), then exercised the canonical Reflex State path and verified provider-health, wire version 1 and LIVE before switching explicitly to the unsupported-version laboratory scenario. The laboratory cleared live view data, displayed `UNSUPPORTED_VERSION` and labelled its error `DEMO_FIXTURE`. Keyboard triggers and 1280x800/390x844 layouts passed. The locally generated screenshot is deliberately excluded from version control as transient browser-test output.
