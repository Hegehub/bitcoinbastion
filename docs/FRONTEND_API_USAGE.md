# Frontend API Usage

The frontend interacts with Bitcoin Bastion through presentation‑safe APIs. Client applications should never handle private keys, wallet seeds or raw Access Pass values in browser code.

## Public APIs

Public endpoints under `/api/v1/public/*` expose status, feature catalog and marketing‑safe data. These calls do not require authentication.

## Proof‑of‑Access flows

For premium features, the frontend must initiate the Proof‑of‑Access flow on behalf of the user:

1. **Create payment intent** – Call `POST /api/v1/access/payment-intents` with the desired plan code and payment method. Redirect the user to BTCPay checkout if required.
2. **Poll payment status** – Poll `GET /api/v1/access/payment-intents/{id}` until `status=paid`.
3. **Issue certificate** – Generate a device keypair in a secure context (not exported to the browser when possible) and call `POST /api/v1/access/certificates` to receive the raw access pass and signed certificate.
4. **Create challenge and session** – Call `POST /api/v1/access/challenges` and then sign the challenge with the device private key. Call `POST /api/v1/access/sessions` to obtain a short‑lived session token.
5. **Sign protected requests** – Attach `X‑Bastion‑Session`, timestamp, nonce, body hash and signature headers as described in `docs/ACCESS_REQUEST_SIGNING.md` to all protected API calls.

Do not store the raw access pass or recovery seed in local storage. The browser is an interface; the device key should live in a secure OS or hardware keystore where possible.

## Prohibited behaviour

- Do not implement email/password login forms. Legacy auth is disabled.
- Do not collect or prompt for Bitcoin wallet seeds or private keys.
- Do not log or export session tokens, signatures, nonces or raw pass values to analytics systems.
- Do not bypass policy checks by tampering with the plan code or scope requests.

Always guide users through the recovery setup flow and remind them that the Bastion Recovery Seed is not a Bitcoin wallet seed. Recovery operations should be initiated from secure devices, not from transient web sessions.
