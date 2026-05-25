# Frontend Performance Notes (Lighthouse-Oriented)

- Keep route payloads mostly static where possible; prefer cached public API reads.
- Avoid heavy client bundles in top-level layout and critical routes.
- Use responsive images and avoid layout shift by declaring dimensions.
- Prefer restrained motion and avoid long-running animation loops.
- Track Lighthouse metrics in CI for LCP, CLS, and INP.
- Treat Lighthouse regressions as release blockers for public pages.
