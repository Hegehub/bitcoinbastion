Current note (2026-06-29): the old Next.js frontend has been removed; historical references below are retained only for migration context. Reflex is the only repository-native frontend.

# Integration Checklist

Status vocabulary: **implemented**, **partially implemented**, **planned**, **blocked**, **not applicable**.

## Backend/API Layer

| Area | Status | Evidence |
| --- | --- | --- |
| Core FastAPI router registration | implemented | `scripts/check_route_api_parity.py` verifies registered routers in `app/main.py`. |
| Trace API contract | implemented | Required Trace endpoints and the public summary endpoint are checked by route parity tests. |
| Webhook management API | implemented | CRUD, test delivery, delivery logs, HMAC signature headers, and delivery log services are present. |
| WebSocket streams | implemented | Generic `/ws/events` and specialized streams are present with topic filtering and payload limiting. |
| Event outbox backbone | partially implemented | Event registry, outbox service, dispatcher, webhook delivery, and WebSocket broadcast plumbing exist; not every planned domain hook is proven by this pass. |
| Plugin API foundation | implemented | Plugin base, registry, permissions, and sandbox files exist. |

## Runtime Profiles

| Area | Status | Evidence |
| --- | --- | --- |
| `deploy/kubernetes/` canonical path | implemented | Runtime profile checker validates canonical overlays. |
| Compose/k8s/k3s/kind/minikube/single-node metadata | implemented | Runtime profile checker validates metadata files and render dry-runs. |
| Bare-metal/systemd documentation | implemented | `docs/BARE_METAL_SYSTEMD.md` documents advanced fallback operation. |
| Kustomize rendering with local kubectl | partially implemented | The checker runs when `kubectl` is available and otherwise records a skipped tool limitation. |

## Frontend Layers

| Area | Status | Evidence |
| --- | --- | --- |
| Legacy Next.js frontend removed | implemented | `docs/OLD_FRONTEND_REMOVAL_REPORT.md` summarises deletion of `frontend/` and CI/compose resources. |
| FastAPI/Jinja `/market` retained | implemented | `/market` remains owned by backend web routes; Reflex does not take it over. |
| Reflex public/Trace/Console routes | implemented | Frontend contract checker validates Reflex routes and ports. |
| Reflex wow layer | partially implemented | Components and route integration exist as preview/operator-visibility surfaces; backend-fed parity is not complete. |
| Safety copy and forbidden wording | implemented | Integration tests verify required safety copy and reject stale `/products`/`/self-host` links in Reflex navigation. |

## Developer Tooling

| Area | Status | Evidence |
| --- | --- | --- |
| Python SDK | implemented | SDK smoke checks validate expected modules and safety guards. |
| TypeScript SDK | implemented | Static SDK contract files and tests are present. |
| CLI | implemented | CLI package exists; this pass treats command behavior as smoke-level only. |
| MCP connector | implemented | MCP package exists; risky actions remain constrained by safety posture. |
