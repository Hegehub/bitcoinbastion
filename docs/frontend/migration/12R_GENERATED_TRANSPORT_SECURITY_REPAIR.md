# Prompt 12R — Generated Transport Security Repair

## Failure chain

| Layer | Expected owner | Before repair | Exact failure | Repair |
|---|---|---|---|---|
| ephemeral device | Prompt-9/11 browser harness | valid, process-memory Ed25519 key | none | unchanged |
| Access/session persistence | backend Access models | active, scoped, device-bound | none | unchanged |
| request PoP | request-bound signer | available in `sitecustomize` only | installer did not survive Reflex worker startup | unchanged signing semantics |
| browser bootstrap | `run_prompt11r_browser.py` | exported legacy marker and secrets | marker had no current generated-provider meaning | select explicit approved profile |
| provider | `RequestSecurityProvider` | structurally compatible but installed by module mutation | provider absent in worker | canonical provider module |
| installer | generated-transport security bridge | `sitecustomize` side effect | worker imported a distinct/unconfigured foundation module | one `install_security_provider` owner |
| transport | `HttpTransport` | fail-closed as designed | `security_provider_required` | app startup installs before State/route imports |
| client | generated `market_similarity_report` | canonical generated client | never reached network | unchanged |
| operation/backend | Feature-67 protected Similarity | canonical PoP/scope validation | no request arrived | unchanged |
| DTO/adapter/State/DOM | Prompt-11 projection | complete | blocked upstream | unchanged |

The first broken boundary was **browser bootstrap → provider installation in the
actual Reflex worker process** (S1/S4/S6). The prior hook mutated a module instance
loaded by Python startup; the generated request constructed a fresh `HttpTransport`
inside the Reflex worker where that mutation was absent.

## Canonical interface and ownership

`RequestSecurityProvider.headers_for` receives the final method, normalized path,
query parameters, and exact canonical body bytes. It returns per-request session
and PoP headers. `HttpTransport` remains the one transport owner used by the
generated Similarity client. `install_security_provider` is the sole installer.
The approved environment bridge is inert unless the exact ephemeral integration
profile is selected and both in-memory inputs exist.

| Operation | Security class | Provider | PoP | Human Intent |
|---|---|---:|---:|---:|
| `market_similarity_report` | protected Access session | required | required | no |
| Market Replay read | public | no | no | no |
| Feature-21 `submit_trace` | public | no | no | no |
| Feature-22 `get_report` | public | no | no | no |

Caller headers cannot replace `Authorization`, `X-Bastion-*`, or any
`Bastion-Request-*` signing header. With no provider, protected operations still
fail before network dispatch. Public Trace remains usable without a provider.

## Rollback

Revert the Prompt-12R commit. Protected Similarity then returns to the previous
fail-closed `security_provider_required` state. This preserves Prompt-11 semantics,
Feature-20, Replay, public Trace Submit/Report, Feature 52/54/67, and persisted data;
it never creates an anonymous protected fallback.
