# Access production frontend and secure device runtime

## Environment

The missing Reflex runtime was **RFX1**: `reflex` and the canonical `uv.lock`
already existed, but the active shell was not using the synchronized frontend
environment. `cd frontend && uv sync --frozen` restores the declared runtime.

## SP1 device provider

Issuance uses SP1: a WebCrypto Ed25519 `CryptoKeyPair`. The private key is
generated non-extractable and stored by structured clone in IndexedDB under the
Access issuance key slot. Only the SPKI public key and its SHA-256 fingerprint
leave the provider. There is no PEM/JWK/raw private-key export and no
localStorage or sessionStorage fallback.

The provider signs the exact backend `canonical_payload` prefixed by the
existing Feature-67 domain-separated message:

`BastionProofOfAccess:v1:access_challenge\n<canonical JSON>`

The older ephemeral request-header signer remains test-only: it reads an
environment-supplied key and signs request digests, not persistent issuance
identity challenges. It is not imported by Access acquisition State.

## State and request ownership

`AccessAcquisitionState` owns safe VMs and lifecycle flags only. Generated DTOs
are adapted immediately. Offer loading, Checkout creation/read, Challenge
creation, PI1 submission, and Grant read all use Feature-53 generated clients.
Checkout and PI1 actions have in-flight guards; generation plus Checkout IDs
reject stale responses. Route transitions clear Challenge, signature, and
public device transients. Success refresh/deep link only calls Grant read.

The signature is a transient transport input, never a browser authorization
boolean. PI1 remains the sole PoP verification and issuance authority.

## Browser proof

`scripts/verify_access_acquisition_browser.py` drives the live Reflex app with
a real backend Offer, one Checkout, canonical integration settlement, the SP1
provider, and PI1. It asserts one Checkout, one Challenge, one Grant, read-only
refresh/deep link, mobile overflow, serious/critical axe findings, and absence
of Access/private-key canaries from browser network text, URL, DOM, and ARIA.

## Rollback

The SP1 scripts, Access State, production Access route rendering, lifecycle
wiring, scenario/tests, and browser harness can be removed independently. A1
and PI1 remain intact. A frontend rollback must make issuance unavailable; it
must not restore placeholder economics, the ephemeral signer, unsigned
issuance, or client-side PoP authority.
