# Bitcoin Bastion Plugin API Foundation

Status: **foundation implemented; production hardening pending**.

The Plugin API foundation defines a safe, auditable extension model for Bitcoin Bastion. It is designed for controlled in-process extensions such as provider adapters, evidence annotations, dashboard panels, scoring rules, treasury checks, policy rules, and delivery-channel proposals.

## What plugins are

Plugins are typed, manifest-first extensions with explicit permissions and sandbox policy. A plugin can only do what its manifest, permission set, and sandbox policy allow.

Initial plugin types:

- `provider`
- `scoring_rule`
- `delivery_channel`
- `dashboard_module`
- `treasury_check`
- `policy_rule`

## What plugins are not

Plugins are not an arbitrary-code marketplace and are not a wallet interface.

Plugins cannot access seed phrases. Plugins cannot access private keys. Plugins cannot access wallet files. Plugins cannot sign Bitcoin transactions. Plugins cannot broadcast Bitcoin transactions. Plugins cannot approve treasury actions.

Plugins can only propose, annotate, emit internal audit events, or provide evidence depending on explicit permissions.

## Manifest-first model

Plugin metadata is represented by `PluginManifest` and can be inspected without importing or executing plugin code. Required fields include:

```json
{
  "plugin_id": "example.provider",
  "name": "Example Provider",
  "version": "0.1.0",
  "description": "Read-only provider adapter.",
  "plugin_type": "provider",
  "entrypoint": "package.module:PluginClass",
  "permissions": ["read:market"],
  "capabilities": ["health_check"],
  "limitations": ["Provider data can be stale or degraded."],
  "safety_flags": {"no_custody": true},
  "enabled_by_default": false,
  "requires_operator_approval": true,
  "supports_dry_run": true
}
```

Invalid plugin identifiers, unknown plugin types, unknown permissions, and custody/signing permissions are rejected during validation.

## API surface

The minimal API is intentionally bounded:

- `GET /api/v1/plugins` lists registered manifests and safety metadata.
- `GET /api/v1/plugins/{plugin_id}` returns a single plugin manifest summary.
- `POST /api/v1/plugins/{plugin_id}/enable` requires admin authorization.
- `POST /api/v1/plugins/{plugin_id}/disable` requires admin authorization.
- `POST /api/v1/plugins/{plugin_id}/dry-run` requires admin authorization and cannot execute risky actions.

No API endpoint loads remote plugin code or accepts secrets, wallet files, or signing material.

## Audit behavior

Registry operations produce structured audit records for:

- `plugin.registered`
- `plugin.enabled`
- `plugin.disabled`
- `plugin.validation_failed`
- `plugin.permission_denied`
- `plugin.execution_blocked`
- `plugin.dry_run_completed`
- `plugin.event_emitted`

Future work may route these records through the internal event outbox after production review.

## Limitations

- External plugin package loading is not enabled.
- Plugin configuration persistence is future work.
- Production auth, review workflows, and rate limits require hardening before marketplace-style use.
- Plugins remain dry-run-first and operator-controlled.
