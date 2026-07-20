# PayRegister LNURL-pay Static QR and NFC

Static PayRegister QR/NFC payloads encode a stable LNURL discovery URL. They are not static BOLT-11 invoices, proof of payment, merchant identity, authorization, custody, or administrative authority.

The flow is: static endpoint resolution → current PayRegister checkout context → LNURL-pay callback → BOLT-11 invoice issuance → independent settlement verification → PayRegister payment proof → receipt creation → optional successAction receipt UX.

Supported endpoint modes are terminal checkout, store open amount, fixed product, and checkout-bound rotating. Terminal and rotating contexts freeze amount, metadata hash, order reference hash, and context version before invoice issuance. Open-amount endpoints enforce explicit min/max millisatoshi bounds.

QR and NFC payloads contain only public discovery data: HTTPS URL, bech32 LNURL, public alias, endpoint mode, display label, and safe merchant description. They never contain a BOLT-11 invoice, callback token, workspace ID, cashier identity, Access Pass, session token, recovery data, wallet seed, or private key.

Callbacks are idempotent for the same immutable payment context and amount. Invoice issued does not mean payment settled. Settlement must match the issued invoice hash and payment hash before the checkout is marked settled, a PayRegister payment proof is created, and a receipt is issued.

Policy hooks protect endpoint creation, checkout publishing, invoice creation, settlement, receipt access, and future refund preparation. Revocation checks can disable endpoints, aliases, terminals, contexts, invoices, and receipt references without deleting audit history.

Customer comments and payerData are untrusted input. They cannot select merchant/store/terminal context, change amount, authorize refunds, assign roles, or bypass settlement verification. Bastion never handles the customer's wallet seed or private key.
