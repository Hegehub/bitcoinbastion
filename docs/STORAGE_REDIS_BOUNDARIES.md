# Redis Boundaries

## 1. Purpose

Redis is an ephemeral runtime store for Bitcoin Bastion. It may improve speed, coordination, short-lived security checks, fanout, and worker behavior, but it must not own canonical platform state.

Redis loss must never destroy critical Bitcoin Bastion truth. PostgreSQL, signed artifacts, object storage metadata, or another explicitly canonical store must remain the authority for durable facts.

## 2. Allowed Redis Use Cases

Redis may be used for these bounded purposes:

- Rate limiting.
- Short-lived challenge cache.
- Short-lived session hot cache.
- Nonce replay cache.
- API response cache for non-critical public data.
- Provider polling temporary state.
- Worker locks.
- Idempotency short-window cache.
- WebSocket fanout.
- Event fanout.
- Celery broker/backend if configured.
- Temporary degraded-mode coordination.

Allowed Redis entries must be rebuildable, naturally expiring, or safe to lose.

## 3. Forbidden Redis Use Cases

Redis must not be the only store for:

- `access_certificates`
- `subscription_entitlements`
- `access_payment_intents`
- `access_revocations`
- `access_audit_events`
- `recovery_quorums`
- `recovery_attempts`
- `treasury_policies`
- `psbt_workflows`
- `business_roles`
- `proof_packet_metadata`
- `storage_artifacts`
- `issuer_keys`
- `device_keys`
- Private keys.
- Seed phrases.
- Wallet files.
- `xprv` / `yprv` / `zprv` material.

If a Redis key mirrors any of these domains, it is a cache only. It must be rebuildable from PostgreSQL, Object Storage metadata, a durable audit log, or another documented canonical source.

## 4. Redis Key Namespace Policy

Use the following namespace convention:

```text
bb:{env}:rate:{scope}:{identity_hash}
bb:{env}:nonce:{session_hash}:{nonce_hash}
bb:{env}:challenge:{challenge_hash}
bb:{env}:session_hot:{session_hash}
bb:{env}:lock:{resource}:{resource_hash}
bb:{env}:fanout:{stream}
bb:{env}:cache:{domain}:{object_hash}
bb:{env}:idempotency:{idempotency_key_hash}
bb:{env}:provider:{provider_name}:poll:{resource_hash}
```

Rules:

- No raw user identifiers.
- No raw IP addresses.
- No raw Bitcoin addresses unless explicitly classified as public and safe.
- No raw access pass tokens.
- No raw API keys.
- No raw invoice IDs if avoidable; use hashes.
- No seed phrases, private keys, wallet files, `xprv`, `yprv`, or `zprv` under any namespace.
- All privacy-sensitive identifiers must be hashed or HMAC-hashed before entering Redis keys or values.

## 5. TTL Policy

Default TTL guidance:

| Redis purpose | TTL guidance |
| --- | --- |
| Rate limit buckets | `<= 24h` |
| Challenge cache | `5-15 minutes` |
| Nonce replay cache | Session lifetime plus safety buffer |
| Session hot cache | `<=` session lifetime |
| Idempotency short-window cache | `24h-72h` |
| Provider polling temporary state | `<= 24h` |
| Public API response cache | Seconds to minutes depending on endpoint |
| Locks | Short TTL required; never indefinite |
| Fanout data | Ephemeral only |

Rules:

- No infinite TTL unless explicitly justified in the code owner review and documented near the caller.
- All locks must have TTL.
- All nonce, challenge, and session-hot keys must expire.
- Cache invalidation must prefer correctness over speed.

## 6. Degraded Mode Behavior

If Redis is unavailable:

- Critical truth must remain available if PostgreSQL and other canonical stores are available.
- Access checks may become slower because hot caches cannot be used.
- Rate limiting may fall back to bounded in-memory mode where implemented.
- WebSocket fanout may degrade or become single-process only.
- Background task coordination may degrade.
- Challenge/session hot checks must fall back to canonical stores where designed.
- No critical security check may silently disappear.

Redis degraded mode must be explicit, observable, and reversible.

## 7. Recovery Behavior

Redis recovery assumptions:

- Redis loss must not cause loss of critical truth.
- Redis restart may invalidate short sessions, challenges, nonces, locks, and hot caches.
- Users may need to re-authenticate or re-sign challenges.
- Workers may need to reacquire locks.
- Caches must rebuild naturally from canonical stores.
- The storage outbox remains in PostgreSQL, not Redis.

## 8. Observability Requirements

Future Redis integrations should expose or feed these metrics/log fields where infrastructure exists:

- `redis_available`
- `redis_latency_ms`
- `redis_error_count`
- `redis_fallback_mode`
- `redis_rate_limit_fallback_count`
- `redis_lock_acquire_failures`
- `redis_cache_hit_count`
- `redis_cache_miss_count`
- `redis_nonce_replay_detected_count`
- `redis_degraded_mode_active`

Logs must identify backend, operation, status, latency, and a hashed or redacted key identifier. Logs must not include raw secrets, raw object bytes, private URLs with credentials, seed phrases, private keys, wallet material, or bearer tokens.

## 9. Security and Privacy Rules

Strict Redis rules:

- Do not store seed phrases.
- Do not store Bitcoin private keys.
- Do not store wallet files.
- Do not store `xprv`, `yprv`, or `zprv`.
- Do not store raw access pass tokens.
- Do not store raw API keys.
- Do not store raw recovery material.
- Do not store raw personally identifying data unless explicitly approved and justified.
- Do not store raw secrets in Redis values.
- Use hashes, HMACs, fingerprints, opaque IDs, or redacted metadata for sensitive identifiers.

## 10. Acceptance Criteria

Redis usage is acceptable only when:

- Redis is documented as ephemeral and non-durable.
- The purpose is listed as an allowed Redis purpose or has an approved architecture note.
- The key follows the `bb:{env}:...` namespace policy.
- Privacy-sensitive identifiers are hashed or HMAC-hashed.
- TTL is finite for locks, nonce caches, challenges, session-hot keys, rate limits, and short-window idempotency keys.
- Canonical state remains in PostgreSQL, Object Storage metadata, durable artifacts, or another explicitly documented source of truth.
- Loss of Redis is tested or documented as degraded mode, not data loss.
