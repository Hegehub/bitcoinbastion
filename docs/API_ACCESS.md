# API Access

Bitcoin Bastion uses Proof-of-Access authorization for protected APIs. Legacy email/password authentication is disabled.

Protected API callers must follow the Access flow:

1. create a payment intent with `/api/v1/access/payment-intents`;
2. issue an Access Certificate and Subscription Entitlement after verified payment;
3. create an origin-bound challenge;
4. sign the challenge with a bound local device key;
5. create a short-lived Proof-of-Possession session;
6. sign protected requests with the required `X-Bastion-*` headers.

Required protected request headers are `X-Bastion-Session`, `X-Bastion-Timestamp`, `X-Bastion-Nonce`, `X-Bastion-Body-Hash`, and `X-Bastion-Signature`.

`Authorization: Bearer` is not accepted as Proof-of-Access, and an Access Pass is never a bearer token.
