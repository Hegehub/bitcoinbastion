# Plugin Permissions

Bitcoin Bastion plugin permissions are deny-by-default. A plugin has no capabilities unless its manifest requests known permissions and the sandbox explicitly allows them.

## Read permissions

- `read:market`
- `read:signals`
- `read:trace`
- `read:evidence`
- `read:onchain`
- `read:wallet_health`
- `read:provider_health`
- `read:policy`
- `read:treasury`

## Bounded write permissions

- `write:evidence_annotation`
- `write:delivery_event`
- `write:operator_note`

These permissions are for controlled annotations or records. They do not imply fund movement, signing, or automatic policy changes.

## Event permissions

- `emit:event`
- `emit:webhook`
- `emit:websocket`

Plugin event emission must go through the internal event/audit adapter. Direct webhook dispatch from plugins is not allowed by default.

## Proposal permissions

- `propose:treasury_action`
- `propose:policy_action`
- `propose:trace_review`

Proposal permissions create review context only. They do not approve, execute, sign, broadcast, or mutate treasury state.

## Admin permissions

- `admin:plugin_enable`
- `admin:plugin_disable`
- `admin:plugin_configure`

Admin permissions must be explicitly allowed and should be reserved for operator-controlled workflows.

## Forbidden permissions

The permission registry rejects custody and signing permissions. Plugins cannot access seed phrases. Plugins cannot access private keys. Plugins cannot access wallet files. Plugins cannot sign Bitcoin transactions. Plugins cannot broadcast Bitcoin transactions. Plugins cannot approve treasury actions.

Forbidden examples include custody-secret access, key derivation, transaction signing, transaction broadcasting, and secret export. If a manifest requests any forbidden permission, validation fails.
