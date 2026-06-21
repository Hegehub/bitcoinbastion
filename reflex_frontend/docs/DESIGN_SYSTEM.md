# Bitcoin Bastion Reflex Design System

## 1. Design principles

The design system is Bitcoin-first, sovereignty-first, no-custody, evidence-oriented, operator-controlled, advisory-only, and transparent about degraded or stale data.

## 2. Color tokens

Colors live in `bastion_ui/theme/tokens.py`. Bitcoin orange is used for emphasis, while dark graphite panels and high-contrast text preserve an operational interface.

## 3. Risk/evidence visual language

Risk and evidence colors must always be paired with text labels such as advisory-only, manual review recommended, limited evidence, provider disagreement, insufficient evidence, elevated risk band, and low confidence. Color alone must not communicate risk.

## 4. Typography

Typography tokens provide readable display, heading, body, caption, mono, code, metric, and label styles. Safety notices must not use tiny text.

## 5. Layout system

Layout primitives include public and console layouts, page shells, containers, sections, responsive grids, two- and three-column grids, stacks, and inline stacks.

## 6. Safety components

Safety components render advisory, no-custody, Trace, Market Intelligence, Treasury review, limitations, and forbidden-input notices. Required copy includes advisory-only, not legal verification, not Bitcoin consensus proof, no custody, public Bitcoin addresses only, and never-enter wallet-secret warnings.

## 7. Degraded/stale states

Feedback components make loading, sanitized errors, degraded data sources, unavailable providers, and stale data visible. Do not hide provider or data failures.

## 8. Accessibility baseline

The foundation includes visible focus styles, readable text sizes, dark-mode contrast, reduced-motion state support, input labels, semantic headings where practical, and non-color-only risk indicators.

## 9. What not to do

Do not request wallet secrets, create transaction signing UI, create auto-execution UI, present Trace as legal verification or Bitcoin consensus proof, present Market Intelligence as financial advice, claim production readiness, or claim Reflex route parity before cutover gates pass.
