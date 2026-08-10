# Feature 67 — Proof-of-Access security shell

Feature 67 is a fail-closed frontend eligibility shell, not an authorization engine. It consumes `HTTP-0019` (`GET /api/v1/access/me`) through the canonical generated client and preserves backend denial as authoritative.

The safe posture keeps session, entitlement, capabilities, PoP, Human Intent, and step-up as distinct dimensions. It has no universal `is_authenticated` or `has_access` flag and its explicit browser allowlist excludes session secrets, challenges, signing material, payment proof, and recovery material. `UNKNOWN` never permits protected rendering.

The route registry binds `/access/security-posture` to security profile `access-session:get_me_api_v1_access_me_get`. Unknown route requirements fail closed. The route initially renders the Access-required/checking shell, so protected content cannot flash before a current posture result. A refresh clears posture before checking again; request generations prevent an older result from overwriting a newer route posture.

The current browser environment has no approved Access/session provider, so the allowed protected path is `NOT_VERIFIABLE_IN_CURRENT_ENVIRONMENT`. This is intentional: `HttpTransport` rejects the protected call at its narrow security boundary rather than accepting a bearer/password/JWT substitute. The denial path is the supported runtime proof. Prompt 16 owns checkout/issuance/PoP, Prompt 17 owns profile/delegation, and Prompt 18 owns recovery/revocation journeys.

Headless Chromium verified the public `/` route, direct protected-route entry, absence of `#protected-content` before and after checking, keyboard activation of `#security-retry`, keyboard focus on `#security-recovery`, the safe `Access required` denial, and responsive behavior at 1280x800 and 390x844. The event traveled over the Reflex event WebSocket; no protected FastAPI request was sent because the canonical transport failed closed before network dispatch. The locally generated screenshot is deliberately excluded from version control as transient browser-test output.

Security posture uses Feature-52 provenance only after a real backend result. Cached or verified-snapshot data never grants current authorization. Payment, entitlement, or PoP alone never grants unrestricted capability.
