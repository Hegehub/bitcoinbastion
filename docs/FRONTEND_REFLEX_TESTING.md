# Reflex Frontend Testing

## 1. Test suite purpose

Prompt 18/22 adds a route, navigation, API-client, Trace-safety, no-custody, Market, Console, and forbidden-wording test baseline for the parallel Reflex frontend. The tests are migration gates: Reflex must remain a non-primary frontend until these tests pass or failures are documented as blockers.

## 2. Route tests

`reflex_frontend/bastion_ui/tests/test_routes.py` verifies public route coverage, dynamic Trace report routes, Proof Packet routes, duplicate route detection, and stale route exclusion.

## 3. Navigation tests

`reflex_frontend/bastion_ui/tests/test_navigation.py` checks main and console navigation constants against canonical route registries and rejects stale `/products` and `/self-host` routes.

## 4. Command palette tests

`reflex_frontend/bastion_ui/tests/test_command_palette.py` verifies required safe commands, command targets, dynamic input flags, safety notes, registered route targets, and absence of risky execution commands.

## 5. API client tests

`reflex_frontend/bastion_ui/tests/test_api_client.py` uses mocked `httpx` transports to validate `BB_API_BASE_URL` configuration, timeout configuration, ResponseEnvelope unwrapping, raw JSON fallback, 400/404/422/429 error normalization, timeout/network error normalization, and endpoint targeting for Public and Trace clients.

## 6. Trace safety tests

`reflex_frontend/bastion_ui/tests/test_trace_safety.py` verifies advisory-only, no-custody, public-address-only, not-legal-verification, not-Bitcoin-consensus-proof, sensitive-material, limitation, low-confidence, and degraded-state Trace copy.

## 7. No-sensitive-input tests

`reflex_frontend/bastion_ui/tests/test_no_sensitive_input.py` validates rejection of seed/mnemonic-like phrases, private-key-like input, xprv/yprv/zprv material, wallet files, keystore JSON-like content, WIF-like material, and signing material without echoing rejected values.

## 8. Forbidden wording tests

`reflex_frontend/bastion_ui/tests/test_forbidden_wording.py` scans Reflex route, component, security, state, service, docs, and test fixture files for forbidden address-morality phrases, with explicit allowlists only for tests that define the forbidden fixtures.

## 9. Market route tests

`reflex_frontend/bastion_ui/tests/test_market_routes.py` verifies Reflex-side Market route registration or explicit delegation metadata and checks that Market copy does not claim production replacement or present analytics as financial advice.

## 10. Console route tests

`reflex_frontend/bastion_ui/tests/test_console_routes.py` verifies Console route registration, navigation parity, module tile coverage, absence of risky execution routes, and review/advisory language for policy surfaces.

## 11. How to run tests

From `reflex_frontend/`:

```bash
uv sync
uv run ruff check .
uv run mypy bastion_ui
uv run pytest
uv run reflex export
```

From the repository root, the broad baseline remains:

```bash
python -m pytest -q
```

## 12. Known limitations

- The tests use mocked API transports and do not require a live FastAPI backend.
- The route registry is a Reflex migration contract and does not change production routing.
- Reflex export can warn about local Node.js versions or generated sitemap files without changing the no-custody test contract.

## 13. Current blockers

Repository-root pytest still includes pre-existing async/test-environment gaps outside the Reflex frontend. Those failures must be resolved before using the root suite as a production cutover gate.
