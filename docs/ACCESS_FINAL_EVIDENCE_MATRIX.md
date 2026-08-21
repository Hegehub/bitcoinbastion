# Access Prompt-16 final evidence matrix

## Security scenarios before A2R2

| Scenario | Browser context/session | Device identity | Checkout | Challenge | Expected result | Existing proof | Missing proof |
|---|---|---|---|---|---|---|---|
| Happy path | A | SP1 Device A | eligible | Device A | issued | PASS | none |
| Wrong device | A + isolated B | A challenge, B signer | eligible | Device A | reject | backend only | isolated browser proof |
| Wrong operation | A | SP1 Device A | eligible | `access.issue` | reject | backend only | second-operation browser proof |
| Expired challenge | A | SP1 Device A | eligible | expired authoritatively | reject | backend only | post-expiry browser proof |
| TOCTOU | A | SP1 Device A | eligible then cancelled | valid | reject | backend only | browser-signature/business-state proof |

## Final browser evidence design

`scripts/verify_access_negative_browser.py` closes the missing cells with two
isolated Playwright contexts. Each context owns a distinct IndexedDB and a
separately generated non-extractable SP1 key. Test setup changes authoritative
SQLite payment, Challenge-expiry, and Checkout-state records; it never changes
Reflex eligibility, seeds a Grant DTO, copies private material, or bypasses PI1.

| Surface | Automated a11y | Keyboard | Mobile | Dark | Light | Secret scan | ARIA scan |
|---|---|---|---|---|---|---|---|
| Offer | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Checkout | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Payment/eligibility | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Security/device step | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Issuing/loading | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Success/Grant | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Expired Challenge | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Wrong device | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Wrong operation | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| Ineligible/TOCTOU | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

The happy-path harness proves production Offer, Checkout, security, issuing, and
Grant rendering. The negative harness scans the canonical safe error semantics
without adding unsafe production controls. Both scan HTTP text, DOM including
ARIA/title/data attributes, URLs, mobile overflow, and serious/critical Axe
violations. Browser traces are not retained.

## Negative network ledger

| Scenario | Checkout mutations | Challenge creations | PI1 attempts | Grants created | Expected |
|---|---:|---:|---:|---:|---|
| Happy | 1 | 1 | 1 | 1 | 1 Grant |
| Wrong device | 1 | 1 | 1 | 0 | reject |
| Wrong operation | 0 | 0 | 0 (one session-operation attempt) | 0 | reject |
| Expired | 1 | 1 | 1 | 0 | reject |
| TOCTOU | 1 | 1 | 1 | 0 | reject |

## Rollback

The negative harness and this evidence record can be removed independently.
Rollback preserves A1, SP1, Access State, PI1, Challenges, Grants, generated
contracts, and production UI, and does not weaken binding, expiry, eligibility,
or secret boundaries.
