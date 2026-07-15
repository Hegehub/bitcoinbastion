# Reflex Accessibility Baseline

Status: **ACTIVE BASELINE / MANUAL AND AUTOMATED PRODUCTION AUDIT PENDING**.

## Accessibility goals

The Reflex frontend should be usable by keyboard and screen-reader users while preserving Bitcoin Bastion safety warnings, degraded-state visibility, and no-custody boundaries.

## Keyboard navigation support

- Skip-to-content links are present in public and console layouts.
- Header, mobile navigation, Console sidebar, and command palette expose text labels.
- Buttons and links are textual, not icon-only.
- Escape/overlay focus-return behavior still needs manual browser review before production cutover.

## Screen-reader support

- Main content regions use `role="main"`.
- Mobile navigation uses navigation labeling.
- Command palette uses dialog labeling.
- Trace address entry has label/help text.
- Degraded and unavailable states include visible text labels.

## Reduced-motion behavior

Reduced-motion helpers and preference state exist. The default posture is conservative: critical information remains visible without animation, and future animated charts must respect reduced-motion state.

## Color contrast notes

Theme tokens favor dark backgrounds with high-contrast foreground text. Warning, degraded, danger, stale, and fallback states must include text labels and cannot rely on color alone.

## Responsive breakpoints

Manual verification should cover 320, 375, 414, 768, 1024, 1280, 1440, and wide Console displays. The layout uses responsive grids, mobile navigation, and wrapping helpers for long addresses, report ids, provider names, and evidence titles.

## Known limitations

Automated WCAG verification has not been completed. Manual audit is still recommended before production cutover.

Existing skip-to-content links, form labels, and alert roles are baseline
implementation evidence only; they are not an accessibility certification.

## Manual verification checklist

- Tab through public routes and Console routes.
- Confirm Shift+Tab reverses focus order.
- Confirm mobile navigation is reachable and labeled.
- Confirm command palette is reachable and labeled.
- Confirm degraded-state copy remains visible at mobile widths.
- Confirm no safety-critical content is hidden by truncation.
