# Bitcoin Bastion Reflex Design System

## 1. Design principles

The Reflex UI foundation is Bitcoin-first, sovereignty-first, no-custody, evidence-oriented, operator-controlled, advisory-only, and explicit about degraded states. It must not claim production parity or certainty that the backend has not proven.

## 2. Color tokens

Color tokens live in `bastion_ui/theme/tokens.py`. Bitcoin orange is used for brand emphasis, while dark panel colors support an operational interface. Risk colors must always be paired with readable labels and advisory language.

## 3. Risk/evidence visual language

Risk and evidence colors indicate bands and confidence context only. They do not imply legal certainty, financial advice, or Bitcoin consensus proof. Use text labels such as `manual review recommended`, `limited evidence`, `provider disagreement`, `insufficient evidence`, `elevated risk band`, and `low confidence`.

## 4. Typography

Typography tokens live in `bastion_ui/theme/typography.py`. Safety notices use readable sizes and must not be hidden in tiny captions.

## 5. Layout system

Layout primitives live in `components/layout/` and include public layout, console layout, shell helpers, container, section, grid, and stack primitives. Full navigation and command palette parity comes later.

## 6. Safety components

Safety components live in `components/safety/` and provide reusable no-custody, advisory, limitations, Trace safety, Market informational, Treasury review, and forbidden-input notices.

## 7. Degraded/stale states

Feedback components live in `components/feedback/`. Degraded, stale, unavailable, and incomplete states must remain visible. Provider or data failures must not be hidden.

## 8. Accessibility baseline

The foundation includes visible focus style tokens, readable type scales, dark-theme contrast, input labels, reduced-motion state support, and non-color-only risk indicators.

## 9. What not to do

Do not request wallet secrets. Do not create signing or auto-execution UI. Do not present Trace as legal verification or Bitcoin consensus proof. Do not present Market Intelligence as financial advice. Do not hide degraded, fallback, stale, unavailable, or low-confidence states.
