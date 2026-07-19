# PayRegister LNURL Cashier and Shift Context

Cashier metadata is operational context, not identity. Lightning Address is payment routing, not authorization. LNURL comment and payerData are not trusted authorization inputs. A cashier cannot approve refunds or payouts unless explicit policy grants a stronger role and step-up.

PayRegister LNURL payment context binds a merchant workspace, store, terminal, terminal device fingerprint, cashier role binding, active shift, order hash, merchant invoice hash, amount, policy hash, and wallet-visible metadata hash. Contexts are canonicalized and hash-bound before invoice issuance; historical settled-payment context must be replaced or adjusted rather than mutated.

Shift lifecycle operations include opening, suspension, resume, close, revoke, and stale-expiry handling. Opening a shift requires an active workspace-scoped role binding, active terminal, active device binding, active PoP session, clean revocation state, and Policy Engine approval. One active shift per terminal is allowed by default.

Wallet-visible LNURL metadata is separate from internal context. It includes concise payment labels, safe store/terminal/order references, and a Lightning identifier, but excludes raw cashier identity, principal hashes, sessions, access passes, policy internals, wallet addresses, device secrets, private merchant notes, and recovery data.

Receipts are issued only after verified settlement and reference cashier/shift context pseudonymously. Receipt packets contain workspace/store/terminal/shift/order hashes, payment proof hash, LNURL payment request hash, amount, settled timestamp, metadata hash, audit event hash, and receipt status.

Revocation of a workspace, store, terminal, cashier role, shift, device, PoP session, Wallet/Lightning Principal, Access Certificate, or offline validity pack blocks new payment contexts. Already-settled payments remain auditable evidence and are not erased by revocation.

Offline/degraded behavior is not implemented as broad offline LNURL-pay support. Future offline validity packs must bind terminal, shift, role, expiry, policy epoch, and revocation epoch, and must never fabricate Lightning settlement confirmation.
