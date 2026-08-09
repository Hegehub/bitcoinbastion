# Prompt 1B0/25 — HTTP Transport Foundation Evidence

Status: **BLOCKED**. The foundation is implemented for two reviewed public reads, but the required representative protected/mutation/special-response set is not authoritative enough to generate safely.

## Foundation delivered

* `NormalizedOperation` is a frozen typed IR covering stable identity, method/path, tag, product, disposition, status, response type, security reference, retry classification, and unique owner.
* Strict Pydantic transport DTOs reject coercion and unknown fields.
* `SafeTransportError` exposes only status, stable code, retryability, safe text, and uncertain-outcome state.
* `HttpTransport` is callable production code, validates responses, never exposes raw bodies, blocks protected calls without an injected boundary, and never automatically retries mutations.
* `generate_http_transport_foundation.py --write|--check` validates runtime operation/schema identities and deterministically emits reviewed bindings and Feature-53 foundation entries.

## Representative set

| Operation | Coverage | Reason |
|---|---|---|
| `GET /api/v1/health` (`HTTP-0076`) | public GET, strict object response, safe HTTP failures | Small stable health contract |
| `GET /api/v1/public/status` (`HTTP-0250`) | public GET, nested envelope, booleans, lists/maps, timezone-aware datetime | Exercises nested strict validation |

The remaining required categories are not claimed. In particular, protected reads/mutations cannot pass `P1B0-A05/A06` because the repository still lacks reviewed dependency-level security projection, and mutation/idempotency/Human-Intent cases cannot be selected without guessing. File/media, union, compatibility, and PayRegister cases also remain unproven in the generator.

## Counts and blockers

* Historical UI candidates: 309.
* Foundation-generated callable owners: 2.
* Feature-53 foundation entries: 2 (Feature 53 remains incomplete).
* Full-set authoritative owners: 0; the fail-closed Stage-1 matrix remains unchanged until Prompt 1B1 authority can be proven.
* `P1B0-B01`: reviewed protected-operation security projection is absent.
* `P1B0-B02`: representative mutation/idempotency/Human-Intent authority is insufficient.
* `P1B0-B03`: generator supports two fixed public schemas, not the full strict OpenAPI schema vocabulary or failure modes required for 309 candidates.
* B05–B13 remain deferred to Prompt 4 with no fabricated versions.

## Full-generation command

The repository-supported interface is `python scripts/generate_http_transport_foundation.py --write` and its verification form is `python scripts/generate_http_transport_foundation.py --check`. It is intentionally still a foundation command, not a claim that full generation is ready.

## Rollback

Remove the transport package, generator, foundation tests, and this evidence file together. Keep the fail-closed ownership matrices and Prompt-4 WebSocket blockers. Rollback must not present the two generated foundation bindings as full-set authority or restore fabricated owner strings.
