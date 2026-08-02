# Wallet/LNURL protected route matrix

Runtime FastAPI dependencies are authoritative; this matrix is an operational
review aid, not an authorization mechanism.

| Method | Path family | Class | Actors | Session | Scope/capability | Assurance / step-up | Offline | Policy action | Audit |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/v1/wallet-auth/{register,login,challenges,recovery/start}` | AUTH_BOOTSTRAP | wallet candidate | no | protocol validation | structured wallet proof | no | bootstrap-specific | security transitions |
| GET/POST | `/v1/wallet-auth/me,entitlements,devices,wallets,step-up` | PROTECTED | Bitcoin/Lightning principal | PoP | server entitlement | standard; step-up endpoint proves fresh intent | no | route operation ID | allow/deny |
| DELETE | `/v1/wallet-auth/devices/*`, `/wallets/*` | HIGH_RISK | root principal | PoP | binding management | action-bound fresh step-up | no | route operation ID | always |
| POST | `/v1/wallet-auth/lockdown` | HIGH_RISK | root/quorum/recovery actor | PoP or recovery policy | lockdown | policy-selected high assurance | no | lockdown | always |
| GET | `/v1/lnurl/auth/callback`, `/pay/callback/*`, `/pay/verify/*`, `/withdraw/callback/*` | AUTH_BOOTSTRAP | protocol wallet | no | k1/payment/withdraw state | protocol proof | no | protocol-specific | transitions/failures |
| POST | `/v1/lnurl/auth/step-up` | PROTECTED | Lightning principal | PoP | requested action | creates fresh Human Intent proof | no | LNURL step-up | always |
| POST | `/v1/lnurl/withdraw/requests` | HIGH_RISK | allowed principal/business role | PoP | payout capability | fresh action-bound proof as policy requires | no | valuable_lnurl_withdraw | always |
| GET/POST | private metrics and Trace | PROTECTED | entitled actors | PoP | scope + metric entitlement | policy-selected | explicit read-only pack only | metric/read action | policy-configured |
| POST/DELETE | policy, treasury, API keys, webhooks | HIGH_RISK | principal/business/enterprise actor | PoP | route scope | fresh Human Intent; quorum where required | no | declared route action | always |
| POST | PayRegister terminal operations | BUSINESS | bound terminal/cashier | PoP or verified offline pack | terminal/shift scope | role and policy | explicit low-risk operations only | terminal action | security transitions |

Recovery-locked and lockdown principals are denied normal protected access.
Access Certificates can raise assurance but remain device-bound, revocable,
non-bearer policy inputs.
