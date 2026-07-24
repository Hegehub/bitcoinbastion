# Bastion LNURL Payment Proofs

A Bastion LNURL Payment Proof proves that a specific server-created Lightning payment request was verified as settled. It does not authenticate the user, create a PoP session, issue an Access Certificate, create a Subscription Entitlement, or independently authorize API access.

## Flow

LNURL-pay request → BOLT-11 invoice issued → settlement verified → LNURL Payment Proof issued → Subscription Entitlement binding in Prompt 33.

Invoice issuance is never settlement. Browser redirects, LNURL `successAction`, frontend status, comments, payerData claims, and unverified webhooks are forbidden trust signals.

## Supported settlement methods

Payment Proof issuance consumes the LNURL settlement verifier result. Accepted settlement methods are internal Lightning node, BTCPay, trusted Lightning provider, LNURL-verify, preimage verification, and explicit test settlement only in development/test policy.

## Canonical proof structure

The canonical unsigned payload is versioned and includes proof identity, payment request ID, HMACed payment hash, invoice hash, callback hash, verification reference hash, context/product, amount, currency, network, settlement method/timestamps, metadata hash, optional principal binding, optional payerData hash, optional preimage commitment, issuer key ID, epochs, and created timestamp.

The proof fingerprint is `SHA256(canonical_json(unsigned_payment_proof_payload))`. The issuer signature is Ed25519 over the LNURL payment proof signing context. No fake PQ or hybrid signature claim is made.

## Privacy model

Payment Proofs do not store or return raw invoices, raw preimages, raw callback URLs, raw verify URLs, raw payerData, wallet keys, Access Passes, session tokens, or issuer private keys. Payment hashes are HMACed for lookup/linkage privacy, invoices are represented by hashes, and preimages are represented only by commitments when available.

## Principal binding

Principal binding is explicit. Supported binding methods are existing PoP session, verified LNURL-auth, verified payerData auth, business workspace context, PayRegister terminal context, and unbound payment. Email/name identifiers, comments, Lightning Address strings, and payerData without server-side verification cannot bind identity.

## Idempotency

The service enforces one logical proof per payment request/payment hash/invoice hash through repository uniqueness semantics. Duplicate callbacks and duplicate settlement verification results return the existing proof.

## Audit, revocation, and disputes

Successful issuance emits `lnurl_payment_proof_created`; failures emit `lnurl_payment_proof_failed` when an audit chain is configured. Proofs are immutable evidence but may be marked revoked/disputed for fraudulent settlement, provider reversal, duplicate mapping, incorrect product binding, compromised issuer key, administrative dispute, or test cleanup. Revocation never deletes settlement history.

## Entitlement handoff

After successful proof issuance, the service emits an internal `lnurl.payment_proof.issued` event containing safe identifiers and hashes for Prompt 33. The event does not issue entitlements or grant access.

## Limitations

The in-memory repository is for service and test wiring. Production deployments should back the repository with the `lnurl_payment_proofs` table and unique constraints for proof ID, payment request ID, payment hash, and invoice hash when the migration sequence is ready.
