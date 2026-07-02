# Secrets

Owns secret injection policy, rotation guidance, environment templates, secret-manager integration and production secret hygiene.

Current canonical paths:

- `.env.example`
- Kubernetes/production secret references under `deploy/`
- security documentation under `docs/`

Migration rule: this layer may document secrets and templates, but it must never contain real secret material.
