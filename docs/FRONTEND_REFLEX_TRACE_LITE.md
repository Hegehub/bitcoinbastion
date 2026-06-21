# Reflex Trace Lite Public Flow

## 1. Routes implemented

Prompt 7 implements the first public Trace Lite entrypoints in the parallel Reflex frontend:

- `/check`
- `/trace`

These routes accept public Bitcoin addresses only and render an advisory Trace Lite flow. They do not implement `/trace/[report_id]` or `/trace/[report_id]/proof-packet`.

## 2. Backend endpoints used

The Trace Lite client uses:

- `/api/v1/trace/lite/{address}`

The shared API client continues to provide base URL handling, timeout behavior, ResponseEnvelope `.data` unwrapping, and safe error normalization.

## 3. Address validation behavior

The frontend accepts plausible public Bitcoin addresses beginning with:

- `bc1`
- `1`
- `3`

Validation is intentionally not a full Bitcoin consensus validator in Prompt 7. It is a frontend safety gate that rejects empty input, obvious non-address text, and wallet-secret-like material before any API call is attempted.

## 4. Sensitive input rejection behavior

The frontend rejects likely sensitive wallet material before backend submission, including:

- seed or mnemonic phrases
- 12-word or 24-word mnemonic-like text
- private-key wording
- WIF-looking private keys
- `xprv`, `yprv`, `zprv`, and `tprv`
- `wallet.dat`
- keystore material
- JSON key material
- signing material

The user-facing rejection message is:

> This looks like sensitive wallet material. Bitcoin Bastion Trace only accepts public Bitcoin addresses. Never enter seed phrases, private keys, wallet files, or signing material.

## 5. Safety copy

The Trace Lite flow must visibly include:

- Advisory-only.
- Not legal verification.
- Not Bitcoin consensus proof.
- No custody.
- Public Bitcoin addresses only.
- Never enter seed phrases, private keys, wallet files or signing material.

## 6. Known limitations

- Trace Lite displays advisory context only.
- Full Trace report pages are not implemented in Prompt 7.
- Proof Packet and Evidence deep UI are not implemented in Prompt 7.
- The result card links to future report work only as development copy when a `report_id` exists.
- Backend response fields are normalized best-effort into a frontend Trace Lite DTO.

## 7. Remaining work for Prompt 8/22

Prompt 8 should implement `/trace/[report_id]`, detailed panels, report loading, and safe report-level degraded states.

## 8. Remaining work for Prompt 9/22

Prompt 9 should implement `/trace/[report_id]/proof-packet`, Proof Packet display, Evidence linkage, and related limitations copy.

## 9. Prompt 8/22 Trace Report Dynamic Routes

Prompt 8 adds the dynamic Reflex report routes:

- `/trace/[report_id]`
- `/trace/[report_id]/proof-packet`

The report route uses the shared Trace API client for public summary, report, evidence, privacy, origin, source-summary, provider-disagreement, UTXO hygiene, dust radar, counterparty lens, and policy-facts endpoints. The UI is panel-based and must keep degraded, limited, stale, or unavailable states visible.

The proof-packet route calls `/api/v1/trace/report/{report_id}/proof-packet`. If the endpoint is missing or restricted, the Reflex UI shows that the proof packet is unavailable and does not fabricate hashes, metadata, sources, or packet content.
