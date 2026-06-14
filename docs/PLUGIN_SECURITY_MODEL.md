# Plugin Security Model

Bitcoin Bastion plugins are designed around explicit limits rather than trust in plugin code.

## Default sandbox

If no sandbox configuration is provided, the default policy is restrictive:

- network access: `false`
- filesystem access: `false`
- secret access: `false`
- requires operator approval: `true`
- dry-run required: `true`
- payload size limit: bounded
- event emission limit: bounded

This means a plugin cannot perform useful work until an operator and the registry explicitly approve permissions and execution mode.

## Dry-run-first behavior

Dry-run is the only safe execution mode in the foundation. Dry-runs may validate payload shape, describe what a plugin would do, and surface limitations. Dry-runs must not send external messages, mutate treasury state, approve policy actions, sign transactions, or broadcast transactions.

## Treasury and policy posture

Treasury plugins are checks only. Policy plugins evaluate context only. They can produce warnings, failed checks, evidence references, and approval requirements. They cannot approve treasury requests or execute risky workflows.

## Secret handling

Plugins cannot access seed phrases. Plugins cannot access private keys. Plugins cannot access wallet files. Plugins cannot request xprv/yprv/zprv material. Plugins cannot handle signing material.

## Observability

Plugin registry operations create structured audit records for registration, enablement, disablement, blocked execution, validation failures, permission denials, and dry-run completion. These records are intentionally bounded and avoid arbitrary high-cardinality labels.

## Future marketplace path

A future marketplace can build on this foundation only after additional controls exist:

- package signature verification
- persisted operator approval state
- production rate limits
- security review gates
- explicit configuration scopes
- compatibility tests for each plugin type

Until then, the foundation supports built-in and in-process plugin interfaces only.
