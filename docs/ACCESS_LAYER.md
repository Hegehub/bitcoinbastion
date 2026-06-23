# Bastion Proof-of-Access Auth PQ Access Layer

This document introduces a new access-layer architecture for Bitcoin Bastion
that replaces traditional email/password authentication with cryptographic
entitlements. It defines the key components and flows required to issue,
validate and use **Bastion Access Passes**.

## Overview

A user purchases access to Bastion via a Lightning invoice, BTCPay invoice
or on‑chain Bitcoin payment. The backend derives a payment proof and issues
a **signed access certificate** bound to a device public key. The certificate
grants rights to a subscription tier (Lite, Base, Plus, Pro, Business or
Enterprise) and a set of API scopes. A local vault on the user's device
holds the private key and signs all authentication challenges.

Access is not tied to an email address or password. Instead, clients prove
possession of the certificate and private key, and the backend uses a policy
engine to decide whether to allow an API request based on the subscription
entitlements, metric credits, risk analysis and revocation status.

## Key Concepts

- **Payment Proof** – a record of a paid invoice. It stores only hashed
  identifiers, timestamps and the purchased tier, avoiding any personally
  identifiable information.
- **Access Certificate** – a signed document that binds a tier, scopes and
  device public keys together. It includes cryptographic commitments
  (`pass_commitment` and `pass_lookup_hash`) and may embed a post‑quantum
  signature alongside a classical signature.
- **Subscription Entitlement** – describes the subscribed plan and associated
  limits, such as allowed metric groups, history range, request rates and
  number of child API keys.
- **API Entitlements** – fine‑grained limits on metrics access, such as
  `max_history_days`, `min_interval` and websocket stream limits.
- **Policy Engine** – evaluates whether a request should be allowed, denied
  or require additional confirmation based on the certificate, subscription
  entitlements, quotas and risk score.
- **Proof‑of‑Possession Session** – after the client proves possession of the
  device key, a short‑lived session token and session key pair is issued.
  All API requests must be signed with the session key and include
  nonces and timestamps to prevent replay.

## Flow

1. **Payment** – The user initiates a payment for a tier. The payment service
   creates a `PaymentProof` with pending status and returns an invoice.
2. **Proof Receipt** – Once payment is settled, the payment proof is marked
   as `paid` and becomes eligible for certificate issuance.
3. **Certificate Issuance** – The certificate service generates a new
   `AccessCertificate` bound to the provided device public keys and the
   purchased tier. A subscription entitlement and API entitlements may be
   attached.
4. **Challenge and Session** – To begin an authenticated session, the client
   requests a challenge, signs it with their device private key, and submits
   the signature. The server verifies the signature and issues an
   `AccessSession` with a session token and session public key.
5. **Request Signing** – Every API request includes the session token,
   timestamp, nonce and a signature computed over the HTTP method, path,
   body hash and metadata. The backend validates the signature, checks
   quotas and uses the policy engine to allow or deny the request.

## Files

- `app/access_layer/models.py` – defines the core data models for payment
  proofs, access certificates, subscription entitlements, API entitlements
  and sessions.
- `app/access_layer/services.py` – outlines services for creating payment
  intents, issuing certificates and managing proof‑of‑possession sessions.
- `app/access_layer/policy.py` – provides a minimal policy engine with
  enumerated policy decisions.
- `app/access_layer/schemas.py` – defines Pydantic request/response schemas
  for integration with the FastAPI routes.

These components form the foundation of a crypto‑auth layer that can
integrate with the existing FastAPI codebase. They do not include any
cryptographic operations, payment integrations or database storage; real
implementations must fill in those details.
