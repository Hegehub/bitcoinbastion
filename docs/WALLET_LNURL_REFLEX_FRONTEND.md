# Wallet-first and LNURL Reflex Frontend

## Security boundary

The canonical frontend lives in `frontend/bastion_ui` (the repository has no separate `reflex_frontend/` application). The frontend is not the authorization authority. It presents backend decisions, requests explicit proof or step-up, and renders entitlements. It never derives permission, assumes challenge validity, assumes payment settlement, or grants a role from local state.

Wallet proof and LNURL-auth establish proof inputs. A Principal, Device Binding, PoP Session, Subscription Entitlement, Policy Engine decision, Audit Chain, and Revocation Registry remain distinct backend-controlled layers. Wallet-first is not wallet-only; LNURL-native is not LNURL-only.

## Routes and components

Wallet entry and lifecycle routes live under `/wallet-auth`, including registration, login, devices, subscription, step-up, Recovery Capsule, Lockdown, Lightning login/pay/withdraw/addresses, and security. Access Certificate and Offline Validity Pack remain secondary high-assurance pages under `/access`.

Reusable components render no-custody warnings, structured wallet intent, locally generated LNURL QR, Device Binding, PoP session metadata, entitlement/payment states, Lightning Addresses, withdraw safety, quorum, recovery, and Lockdown. The established Reflex cards, responsive grids, graphite/black/orange theme, and accessibility attributes are reused.

## State architecture

Specialized Reflex state modules track only presentation-safe fields:

- `wallet_auth_state`: challenge identifiers, canonical human intent, safe Principal/Device/session summaries; proof signatures are submitted from local event input and never assigned to state.
- `lnurl_auth_state`: encoded LNURL, expected domain, action, expiry, and status; raw k1/linking keys are discarded.
- `lnurl_payment_state`: payment reference, plan, invoice, settlement, and entitlement states; invoice issuance never activates entitlement.
- `lnurl_withdraw_state`: policy and payout presentation; it publishes a QR only after `policy_approved=true`.
- `wallet_device_state` and `wallet_recovery_state`: safe backend summaries without keys or recovery proof material.

Async service clients under `services/` use the shared envelope/error transport and exact implemented routes. Central PoP signing uses a non-exportable signer adapter and production headers; raw session/device material is not Reflex public state or persistent browser storage.

## Backend contract gaps

The current LNURL router does not expose an auth-attempt status endpoint or withdraw-status endpoint. Therefore the frontend cannot truthfully complete bounded auth polling or payout polling. It shows an unavailable/degraded state rather than fabricating success. A deployment browser/Vault bridge providing a non-exportable Device key is also required for end-to-end PoP session use. Real wallet compatibility and backend capability-registry endpoints remain deployment work.

## Manual QA

- Desktop and mobile LNURL login: domain/action/expiry, local QR, copy and open-wallet fallback.
- BIP-322: full structured intent, proof import, replay/expiry, compatibility limitation.
- New Device Binding and session expiry/revocation.
- Subscription request, invoice-issued, pending, verified settlement, entitlement issuance, safe successAction.
- Lightning Address routing and privacy-first payerData/comment handling.
- Refund/withdraw denial, step-up, approval, expiry, and missing status contract.
- High-risk step-up Human Intent and quorum.
- Recovery Capsule factors/cooldown and Lockdown start/release.
- Access Certificate and Offline Validity Pack limitations.
- Keyboard, screen-reader, text-only status, mobile deep link, reduced motion, and no hover-only security copy.

Passing UI tests is not a production-readiness claim. Callback security, policy/revocation, settlement providers, real-wallet interoperability, browser Device signer integration, and the missing status APIs block production release.
