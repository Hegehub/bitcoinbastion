# Frontend Routes

Wallet-first entry routes are `/access` and `/wallet-auth`. Authentication routes include `/wallet-auth/register`, `/wallet-auth/login`, `/wallet-auth/lnurl`, `/wallet-auth/bitcoin`, `/wallet-auth/session`, `/wallet-auth/devices`, `/wallet-auth/entitlements`, `/wallet-auth/step-up`, `/wallet-auth/recovery`, and `/wallet-auth/lockdown`.

Payment routes are `/access/plans`, `/access/checkout`, `/access/payment`, `/access/payment/pending`, `/access/payment/success`, `/lnurl/pay`, and `/lnurl/payment-status`. `/lnurl/auth` explains the implemented callback contract and the missing frontend status endpoint. Optional high-assurance pages are `/access/certificate` and `/access/offline`; unsupported actions remain unavailable.

Business/PayRegister information pages exist at `/business/access`, `/business/devices`, `/business/security`, `/register/access`, `/register/devices`, and `/register/refunds`. They do not infer role permissions or create refunds locally; backend policy and step-up remain authoritative.
