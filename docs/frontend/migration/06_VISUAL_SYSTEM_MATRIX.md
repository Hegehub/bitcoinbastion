# Prompt 6 Canonical Visual System Matrix

## Recovered feature ownership

| Feature | Canonical repository name | Prompt-6 evidence | Coverage |
|---:|---|---|---|
| 01 | Bitcoin.org-inspired semantic theme contract | typed light/dark palettes and CSS role contract | IMPLEMENTED_VERIFIED |
| 02 | Optical Liquid Glass surfaces | bounded material hierarchy and representative glass navigation/panels | IMPLEMENTED_VERIFIED |
| 03 | Adaptive glass text contrast | mode-specific text/surface roles plus contrast validator | IMPLEMENTED_VERIFIED |
| 04 | Reduced-transparency solid fallback | `prefers-reduced-transparency`/forced-colors glass→matte CSS | IMPLEMENTED_VERIFIED |
| 05 | Light, dark and high-contrast modes | native Reflex color mode and forced-colors fallback | IMPLEMENTED_VERIFIED |
| 06 | Semantic color invariants without blue/cyan | brand/semantic separation; olive information role; blue audit | IMPLEMENTED_VERIFIED |
| 07 | Living topology geometry background | pointer-inert grid/node ambient layer | IMPLEMENTED_VERIFIED |
| 08 | Data-driven pattern intensity | typed low/normal/high intensity API; consumer uses neutral default without recomputing backend truth | IMPLEMENTED_VERIFIED |
| 09 | Static low-power/reduced-motion pattern | compositor transform only; static under reduced motion | IMPLEMENTED_VERIFIED |
| 11 | State-aware glass edge highlight | semantic borders remain independent of brand | IMPLEMENTED_VERIFIED |
| 12 | Glass focus/selection lens | three-pixel semantic focus ring plus non-color active state | IMPLEMENTED_VERIFIED |
| 50 | Glass performance quality ladder | solid/matte/three bounded glass levels | IMPLEMENTED_VERIFIED |
| 51 | Surface material, matte intensity, transparency and contrast debug overlay | development-only safe diagnostics plus deterministic validator | IMPLEMENTED_VERIFIED |

Later domain prompts may pass safe view-model intensity to Feature 08; the visual layer never derives backend conclusions. Feature 51 diagnostics remain development-only. No later domain screen is promoted by this matrix.

## Token and material matrix

| Primitive | Dark | Light | Reduced transparency/motion | Consumers | Accessibility/performance |
|---|---|---|---|---|---|
| background/elevated/surface | near-black/graphite | warm white/neutral | unchanged solid hierarchy | shell, cards | primary contrast ≥ 7:1 |
| brand | Bitcoin orange `#F7931A` | accessible dark orange `#C76500` | unchanged | primary button, links, focus-adjacent emphasis | never warning/error/verified |
| semantic states | green/yellow/red/olive | darker green/ochre/red/olive | text and border remain | badges, alerts, lifecycle | never color-only |
| typography | system sans + system mono | same | no motion dependency | all primitives | compact operational scale |
| spacing | 4–48 px scale | same | same | shared primitives | density retained |
| radius | 8/12/16/22/pill | same | same | cards, inputs, buttons | bounded family |
| shadows | low/medium/high | same tiers | borders preserve hierarchy | elevated/overlay only | no shadow-only meaning |
| solid | graphite | warm neutral | unchanged | dense/security content | no blur |
| matte | 94% dark | 95% light | canonical fallback | ordinary cards/tables | no backdrop cost |
| glass subtle | 10 px | 10 px | matte/no blur | navigation | one large chrome surface |
| glass elevated | 16 px | 16 px | matte/no blur | selective panels | bounded shadow |
| glass overlay | 20 px | 20 px | matte/no blur | future overlay owner | not used full-screen |
| motion | 0/120/180/320 ms | same | animations collapse to static | buttons/ambient | transform/opacity only |
| layers | 0/20/30/40/50/60 | same | same | base/sticky/popover/overlay/modal/toast | no arbitrary huge index |

## Deterministic inventory

At implementation time the frontend contained 340 production Python files, 48 hardcoded six-digit hex occurrences, 5 `backdrop_filter` references, 8 `box_shadow` references and 5 animation declarations. Canonical primitives account for the shared material/effect references. Remaining literals are classified below rather than globally replaced.

## Brand and semantic audits

* Canonical brand role: orange only. No blue-family value is used by canonical brand, focus, selected or action roles.
* `#3B82F6` remains only as the explicitly labeled legacy/data-series compatibility token; it is not consumed as brand.
* Information uses a muted olive role so it cannot be confused with Bitcoin brand orange.
* Success, warning, error, provenance, security, Market series and Evidence states remain independent.
* Orange primary uses: Bitcoin identity, primary action, and restrained selection emphasis. Warning uses ochre, not brand orange.

## Legacy visual debt

| Debt | Classification | Later owner |
|---|---|---|
| remaining component-local hex literals | legacy or data-visualization exception; 48 inventory occurrences before focused migration | owning domain prompts 8–23 |
| older component-specific cards/panels | legacy duplicate; canonical shared cards migrated first | owning domain prompt |
| legacy dark-only token aliases | compatibility boundary for old tests/components | Prompt 25 cleanup after consumers migrate |
| chart series colors | intentional data-semantic exceptions | chart/domain prompts 10–11 |
| old animation dictionaries | legacy; reduced-motion global guard makes them safe | Prompt 25 cleanup |
| theme/App and RouterData deprecations | framework migration debt, not visual semantics | dependency/cleanup prompt 24–25 |

## Rollback

Revert Prompt-6 token/material/CSS and representative consumer changes together. Independent rollback may remove ambient geometry, native theme toggle, material variants or validators while retaining route IDs, Feature-58 flags, HTTP/WS contracts, Feature-52 provenance, Feature-67 posture, lifecycle State and user data. Never restore dark-only unreadable surfaces or color-only focus/security states.
