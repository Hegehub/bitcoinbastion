# Prompt 7 Canonical Application Shell Matrix

## Recovered feature ownership

| Feature | Canonical repository name | Implementation | Coverage |
|---:|---|---|---|
| 10 | Shared liquid active-tab indicator | canonical `aria-current` cue with text, border and reduced-motion-safe material response | IMPLEMENTED_VERIFIED |
| 37 | Safety-aware command palette | typed local route commands filtered by Feature 58 and Feature 67 discoverability | IMPLEMENTED_VERIFIED |
| 38 | Keyboard shortcut layer | accessible `/` access key, arrows, Enter, Escape and focus return | IMPLEMENTED_VERIFIED |
| 48 | Mobile action dock and table transformations | shared mobile toolbar, canonical drawer, safe areas and labelled responsive tables | IMPLEMENTED_VERIFIED |
| 57 | Legacy `/console/wow` redirect and migration telemetry when required | internal-only deprecated alias to Command Center; no telemetry sink is required | IMPLEMENTED_VERIFIED |

## Shell matrix

| Primitive | Route dependency | Desktop/mobile | Keyboard | Theme/motion | Security/flag/lifecycle |
|---|---|---|---|---|---|
| `app_shell` | current canonical route identity | one root; responsive content and safe-area dock | skip link and landmarks | Prompt-6 tokens and ambient owner | stores no domain/security/transport data |
| route context | `ROUTE_BY_ID`, hierarchy | product/domain and canonical breadcrumbs | link traversal; current-page semantics | theme roles; static | safe metadata only |
| header | canonical navigation | desktop and same-registry mobile trigger | links, command, theme, menu | glass→matte; reduced motion | public/access-aware entries only |
| command overlay | canonical commands | bounded desktop/mobile dialog | search, arrows, Enter, Escape, focus return | glass overlay; static fallback | disabled/denied omitted; backend authorization still wins |
| mobile drawer | Prompt-5 eligibility | grouped narrow overlay | close/select focus return | same tokens; safe-area padding | same flags/routes; no second taxonomy |
| mobile dock | Feature 48 actions | narrow only | labelled buttons | bounded glass/matte | no mutation bus |
| responsive table | table semantics | contained scroll and named cells | native table traversal | no animation | data ownership unchanged |

## Command matrix

Commands are generated as `navigate.<route-id>` from canonical navigation
metadata. Each has type `NAVIGATION`, a route ID, domain, aliases, keywords and
stable order. Paths resolve only at activation. Search ranks exact label,
label prefix, alias prefix, substring, current-domain relevance, canonical
order and ID without a backend fetch. Protected/operator discovery requires an
explicit current security requirement; Feature 67/backend denial still wins.

The contextual-action contract permits only `REFRESH`,
`COPY_SAFE_IDENTIFIER`, and `NAVIGATE`. It has no generic mutation executor.

## Mobile and Wow matrix

| Effect | Purpose | Reduced motion | Performance |
|---|---|---|---|
| active route indicator | orientation | static border/text remains | transform/border only |
| ambient geometry | bounded depth | one static field | one CSS transform, no State traffic |
| overlay reveal | spatial context | appears immediately | bounded opacity/transform |
| action dock | reachable safe actions | no functional animation | narrow-only; content is not duplicated |

Feature 59/60 laboratories remain development-only and cannot be enabled by a
command. Provenance remains section-owned; the shell never invents aggregate
or `MIXED` provenance.

## Rollback

The shell root, route context, command registry/palette, mobile dock, active
indicator and matrices can be reverted independently, except that removing the
registry also removes its palette consumer. Rollback preserves Prompt-5 route
IDs/flags, Prompt-6 tokens, Feature 52, Feature 67, HTTP/WS ownership, the safe
legacy alias and user data. It must not restore a literal-path command owner or
make `/console/wow` canonical again.
