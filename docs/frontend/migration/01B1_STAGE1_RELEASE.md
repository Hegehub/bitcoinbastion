# Prompt 1B1/25 — Stage-1 HTTP Transport Release

Stage 1 canonically generates the current `AUTHORITATIVE_NOW` HTTP UI set with:

* 286 compiled OpenAPI component schemas;
* 194 strict request bindings;
* 194 typed success bindings;
* 194 safe normalized error aliases;
* 194 async callable bindings over the shared transport;
* 194 exactly-one ownership records;
* 194 Feature-53 entries;
* one deterministic generated-file manifest.

All generated operations are classified `CLIENT_ONLY`. No adapter, view model, Reflex
State, trigger, rendered component, or browser evidence is implied.

Handwritten literal/client paths are non-canonical. Their explicit wrapper, stale-route
or review-required classification lives in `01B1_TRANSPORT_COMPATIBILITY.json`; removal
is deferred until consumer parity is proven rather than performed speculatively.

HTML/callback/protocol/internal and unresolved mutation contracts remain outside generic
active ownership. WebSocket blockers B05-B13 remain transferred to Prompt 4.

Canonical commands:

```text
python scripts/generate_http_transport.py --write
python scripts/generate_http_transport.py --check
python scripts/generate_transport_compatibility.py --write
python scripts/generate_transport_compatibility.py --check
python scripts/validate_frontend_migration_baseline.py
```
