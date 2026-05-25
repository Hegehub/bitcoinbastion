# Frontend Production Readiness

## Accessibility

- Use semantic landmarks (`header`, `main`, `footer`).
- Maintain keyboard access for navigation and command palette.
- Preserve visible focus states for all interactive controls.
- Ensure status states are textually communicated (not color-only).

## SEO

- Use route-level metadata with stable title/description.
- Keep canonical production `metadataBase`.
- Maintain `robots.ts` and `sitemap.ts` with production URLs.

## Performance

- Prefer static generation for content-first pages.
- Keep client components scoped to interactive zones only.
- Avoid unnecessary large client bundles.
- Track Core Web Vitals in production.

## Security headers

Recommended at edge/proxy layer:

- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-Frame-Options: DENY` (or CSP `frame-ancestors 'none'`)
- Content Security Policy tailored for Next.js assets and analytics

## API fallback behavior

- Public pages must tolerate backend unavailability.
- Degraded states must be explicit (never silently shown as healthy).
- Demo/baseline data must be labeled and never presented as verified production evidence.

## Monitoring

- Enable Vercel deployment + runtime logs.
- Capture frontend errors (Sentry or equivalent).
- Track uptime and page-level failures for `/status`, `/evidence`, `/self-host`.

## Rollback

- Use Vercel instant rollback to previous deployment when regressions are detected.
- Keep backend and frontend deploys decoupled for safe rollback.
- Re-run lint/typecheck/test/build and smoke-check key routes before re-promoting.
