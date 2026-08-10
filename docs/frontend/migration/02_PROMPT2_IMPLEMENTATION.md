# Prompt 2 implementation: safe projections and provenance

## Evidence boundary

Current Stage-1 artifacts validate against their recorded source revision. The historical objects `0ff0049114b864079ed7aabbc3272c82b5d9b106` and `360e85a0825ffdfc93b68a182594963930342b96` are absent, so their comparison is `NOT_VERIFIABLE_HISTORICAL_OBJECT_UNAVAILABLE`; this is not presented as a current contract failure.

## Canonical architecture

The only supported direction is `generated DTO -> domain adapter -> safe view model -> Reflex State -> component`. Overview, Operations, Market, Trace, Evidence, Access, Console, LNURL, and PayRegister own separate adapters; PayRegister is not a Core adapter. View models expose explicit browser allowlists and never serialize transport objects by default.

Feature 52 is implemented by `ProvenanceState`, which contains exactly `LIVE`, `VERIFIED_SNAPSHOT`, `DEMO_FIXTURE`, and `UNAVAILABLE`. Snapshot provenance requires revision, capture time, and integrity identity. Quality (`stale`, `partial`, `degraded`, `conflicting`) is orthogonal and remains section-local. The shared badge always renders text plus a non-color bullet and exposes an accessible name.

Feature 54 is implemented through typed Overview, Operations, and Access adapters. These preserve nullable values, booleans, empty collections, `Decimal` precision, units, aware datetimes, source maps, limitations, and backend quality flags. The Access child-key projection deliberately excludes `raw_child_api_key`.

## Canonical harness

The side-effect-free journey is `HTTP-0250`, `GET /api/v1/public/status`, operation `public_status_api_v1_public_status_get`. Reflex invokes the generated callable through `HttpTransport`; it does not duplicate a literal HTTP client.

| DTO field | Adapter/view model | State/computed field | DOM |
| --- | --- | --- | --- |
| `data.platform_status` | `PublicStatusViewModel.platform_status` | `Prompt2StatusState.platform_status` | `#status-platform` |
| `data.trace_status` | `PublicStatusViewModel.trace_status` | `Prompt2StatusState.trace_status` | `#status-trace` |
| `data.last_update` | `PublicStatusViewModel.last_update` | `Prompt2StatusState.last_update` | `#status-updated` |
| runtime source | `PublicStatusViewModel.provenance` | `Prompt2StatusState.provenance_state` | `[data-provenance=LIVE]` |

The lifecycle distinguishes loading, empty, unavailable/offline, 401, 403, 404, 409, 422, 429, and server errors. Request generations implement latest-request-wins; cancellation invalidates the active generation; retries are bounded to metadata-approved GETs, never generic mutations.

## Browser evidence

Headless Chromium exercised the real Reflex application at `/status`: keyboard focus plus Enter triggered the event, the Reflex event WebSocket was observed, the server-side canonical client returned `platform_status=baseline` and `trace_status=baseline`, the three named fields and accessible `LIVE` badge appeared, and the page remained functional at 1280x800 and 390x844. The locally generated screenshot is deliberately excluded from version control because it is transient browser-test output. In Reflex, the browser sends the State event over its event WebSocket; the backend-to-FastAPI HTTP leg is server-side and is covered by the canonical-client transport contract test rather than falsely claimed as a browser fetch.

## Remaining work

`02_TRANSFORMATION_INVENTORY.json` records untyped legacy transformations without claiming migration. They retain future domain ownership. No Prompt-3 Access shell, Prompt-4 WebSocket runtime, fixture library, or Prompt-6 redesign is included.
