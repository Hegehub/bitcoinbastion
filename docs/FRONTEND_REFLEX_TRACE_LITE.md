# Reflex Trace Lite Public Flow

## 1. Routes implemented

Prompt 7 implements the first public Trace Lite routes in the parallel Reflex frontend:

- `/check` — focused public Bitcoin address check flow.
- `/trace` — public Trace landing page and alternate entrypoint to the same Trace Lite flow.

Dynamic report routes remain deferred.

## 2. Backend endpoints used

The Reflex Trace Lite client uses the existing backend endpoint:

- `/api/v1/trace/lite/{address}` — preferred lightweight public Trace endpoint.

The older `/api/v1/trace/address/{address}` client method remains available for later detailed flows, but `/check` and `/trace` use the Lite endpoint.

## 3. Address validation behavior

Frontend validation accepts plausible public Bitcoin addresses beginning with:

- `bc1`
- `1`
- `3`

This is not a full Bitcoin consensus validator. It is a frontend safety gate that rejects obvious invalid input and sensitive wallet material before any backend call.

## 4. Sensitive input rejection behavior

The frontend rejects empty input, obvious non-address text, seed/mnemonic phrases, 12-word and 24-word mnemonic-like strings, private-key wording, WIF-looking private keys, xprv/yprv/zprv/tprv strings, `wallet.dat`, keystore references, JSON key material, and signing-material wording.

Rejected sensitive input is not sent to the API client.

## 5. Safety copy

Trace Lite displays required safety copy:

- Advisory-only.
- Not legal verification.
- Not Bitcoin consensus proof.
- No custody.
- Public Bitcoin addresses only.
- Never enter seed phrases, private keys, wallet files or signing material.

## 6. Known limitations

- `/trace/[report_id]` is not implemented in Prompt 7.
- `/trace/[report_id]/proof-packet` is not implemented in Prompt 7.
- Trace Lite maps backend fields best-effort into a frontend DTO.
- Public address validation is intentionally conservative and not a consensus validator.
- Result rendering is advisory and does not imply payment approval, custody, or legal status.

## 7. Remaining work for Prompt 8/22

Prompt 8 should implement dynamic Trace report routes and detailed panels for `/trace/[report_id]`.

## 8. Remaining work for Prompt 9/22

Prompt 9 should implement Proof Packet and Evidence deep UI for `/trace/[report_id]/proof-packet`.
