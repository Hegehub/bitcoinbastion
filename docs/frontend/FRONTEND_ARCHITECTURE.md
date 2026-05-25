# Bitcoin Bastion Frontend Architecture (Production Plan)

## 1) Current Repository Baseline (Verified)

### Backend facts
- FastAPI entrypoint is `app/main.py`.
- Public API router is `app/api/v1/public.py`.
- Public API schemas are in `app/schemas/public_site.py`.
- Public-site services are in `app/services/public_site/`.
- Backend dependency management uses `pyproject.toml`.

### Frontend state today
- A `frontend/` directory exists with a Next.js codebase and test files.
- This plan treats the current frontend as **non-production baseline/prototype** and defines a hardened, production-grade architecture target.

---

## 2) Public API Endpoints Available to the Frontend

The app mounts routes using `settings.api_prefix` (`/api/v1`) plus router prefix `/public`, so public base path is:
- `/api/v1/public`

### Public endpoints
1. `GET /api/v1/public/landing`
   - Response envelope data type: `PublicLandingResponse`
   - Purpose: home page payload (modules, status summary, catalog, roadmap summary, safety principles, links)

2. `GET /api/v1/public/status`
   - Response envelope data type: `PublicStatusResponse`
   - Purpose: platform + trace status strip, module readiness, limitations, update timestamp

3. `GET /api/v1/public/roadmap`
   - Response envelope data type: `PublicRoadmapResponse`
   - Purpose: roadmap phase and implementation distribution

4. `GET /api/v1/public/stats`
   - Response envelope data type: `PublicStatsResponse`
   - Purpose: public-safe metrics and supported modules

5. `GET /api/v1/public/features`
   - Response envelope data type: `list[PublicFeatureEntry]`
   - Purpose: feature catalog cards, filtering by category/status/availability

6. `GET /api/v1/public/trace/{report_id}/summary`
   - Response envelope data type: `PublicTraceSummary`
   - Purpose: read-only advisory trace summary for public report detail pages
   - Returns `404` if report does not exist

### Envelope contract
Public endpoints are wrapped in `ResponseEnvelope[T]`; frontend API client should assume:
- data in `data`
- backend-standard error envelope for non-2xx

---

## 3) Proposed Production Frontend Structure (`/frontend`)

```text
/frontend
  /app
    /(marketing)
      page.tsx
      status/page.tsx
      roadmap/page.tsx
      features/page.tsx
      trace/[reportId]/page.tsx
    /api/health/route.ts
    /layout.tsx
    /globals.css
    /not-found.tsx
    /error.tsx
  /components
    /ui                # shadcn/ui primitives
    /layout            # header/footer/shells
    /marketing         # hero, principles, roadmap teaser
    /status            # strip, cards, module matrix
    /features          # feature grid, filters, states
    /trace             # summary blocks, notices, limitations
    /charts            # recharts wrappers
    /motion            # framer-motion presets
  /lib
    /api
      client.ts        # fetch wrapper, interceptors, error mapping
      public.ts        # public endpoint functions
      keys.ts          # tanstack query keys
      contracts.ts     # zod decoders for envelopes
    /config
      env.server.ts
      env.client.ts
    /security
      csp.ts
      sanitize.ts
    /seo
      metadata.ts
      jsonld.ts
    /utils
      date.ts
      format.ts
  /hooks
    usePublicLanding.ts
    usePublicStatus.ts
    usePublicRoadmap.ts
    usePublicStats.ts
    usePublicFeatures.ts
    usePublicTraceSummary.ts
  /types
    api.ts
    public.ts
  /styles
    tokens.css
  /tests
    /unit              # vitest + RTL
    /contract          # api envelope/schema compatibility tests
    /e2e               # playwright
    /a11y              # axe + focus flow checks
  /public
    /images
    /icons
    robots.txt
    sitemap.xml
  middleware.ts
  next.config.js
  tailwind.config.ts
  postcss.config.js
  tsconfig.json
  vitest.config.ts
  playwright.config.ts
  package.json
```

---

## 4) Production Stack Blueprint

- **Framework:** Next.js App Router (SSR/ISR + route-level loading/error boundaries)
- **Language:** TypeScript strict mode
- **Styling:** Tailwind CSS + design tokens
- **Component system:** shadcn/ui (headless + accessible primitives)
- **Animation:** Framer Motion (subtle, purposeful transitions)
- **Data fetching/cache:** TanStack Query (client cache + retry policies)
- **Data visualization:** Recharts (public stats/status visuals)
- **Icons:** Lucide React
- **Unit/integration testing:** Vitest + React Testing Library
- **End-to-end testing:** Playwright (critical journeys + accessibility smoke)

---

## 5) Frontend Goals

1. Ship a **public, trustworthy, advisory-first** product surface.
2. Keep the public experience **fast, resilient, and cache-efficient**.
3. Make backend contract drift visible early through schema/contract tests.
4. Enforce non-custodial language and safety disclosures across pages.
5. Be deployment-ready for Kubernetes ingress + CDN edge caching.

---

## 6) Target Pages

1. `/` (Landing): hero, principles, module highlights, readiness indicators
2. `/status`: platform + trace status, limitations, last updated
3. `/roadmap`: current phase and staged capabilities
4. `/features`: catalog by category/status/availability
5. `/trace/[reportId]`: advisory trace summary and warnings
6. `/security` (recommended): user-facing trust and disclosure page
7. `/developers` (recommended): API usage and public contract notes

---

## 7) Design System Direction

- **Token-first system:** semantic colors (`surface`, `muted`, `safe`, `warning`, `critical`), type scale, spacing scale.
- **Component tiers:**
  - Tier 1: shadcn/ui primitives (Button, Card, Tabs, Dialog, Tooltip)
  - Tier 2: Bitcoin Bastion composites (StatusCard, SafetyNotice, FeatureModuleCard)
- **Visual language:** confidence-through-clarity; avoid speculative visual metaphors.
- **Motion policy:** low-motion defaults; all key transitions respect `prefers-reduced-motion`.
- **Content conventions:** every risk/status visualization pairs with explicit limitation text.

---

## 8) API Integration Model

- **Route ownership:** all public page data sourced exclusively from `/api/v1/public/*` endpoints.
- **Client architecture:**
  - `lib/api/client.ts`: typed `fetch` with timeout, retry, and envelope parsing
  - `lib/api/public.ts`: endpoint-specific functions
  - hooks use TanStack Query for data + stale policies
- **Validation model:** parse response envelopes with runtime validation (recommended: zod).
- **Error model:** map backend HTTP failures to user-safe UI states.
- **Caching strategy:**
  - SSR for landing + status/roadmap/features where appropriate
  - client revalidation with query stale times per endpoint criticality

---

## 9) Environment Variables

### Required
- `NEXT_PUBLIC_API_BASE_URL` (e.g., `https://api.bitcoinbastion.com`)

### Optional
- `NEXT_PUBLIC_SITE_URL` (canonical metadata base)
- `NEXT_PUBLIC_SENTRY_DSN` (frontend observability)
- `NEXT_PUBLIC_ANALYTICS_ID` (privacy-compliant analytics only)
- `API_REQUEST_TIMEOUT_MS` (server-side fetch timeout)

### Policy
- No secrets in `NEXT_PUBLIC_*` other than public identifiers.
- Validate env at boot in `lib/config/env.*` and fail fast in production.

---

## 10) Deployment Strategy

- **Build artifact:** immutable Next.js production image.
- **Runtime:** Kubernetes deployment behind ingress/CDN.
- **Caching:**
  - static assets: long cache with content hashes
  - route responses: ISR/edge cache where safe
- **Release flow:**
  1. Build + unit tests
  2. Contract + e2e checks
  3. Deploy canary
  4. Observe error budget and web vitals
  5. Progressive rollout
- **Rollback:** previous image + config snapshot; no schema mutation risk on frontend rollback.

---

## 11) Testing Strategy

### Unit/UI (Vitest)
- Component rendering, fallback states, hooks behavior, envelope parsing.

### Contract tests
- Assert frontend decoders align with `PublicLandingResponse`, `PublicStatusResponse`, `PublicRoadmapResponse`, `PublicStatsResponse`, `PublicFeatureEntry`, `PublicTraceSummary`.

### E2E (Playwright)
- Home, status, roadmap, features, trace detail happy/error paths.
- 404 handling for unknown report id.

### Non-functional
- Lighthouse CI budgets (performance/accessibility/SEO).
- Visual regression snapshots for key pages.

---

## 12) Accessibility Strategy

- WCAG 2.2 AA target.
- Keyboard-first flows and visible focus rings.
- Semantic headings/landmarks, skip links.
- Color contrast validation against token palette.
- Reduced-motion compliance.
- Automated a11y checks in CI + manual screen reader spot checks.

---

## 13) Security Notes

- Treat all API data as untrusted: escape/sanitize outputs.
- Enforce strong CSP, HSTS via ingress and middleware alignment.
- Avoid exposing internal API topology in client errors.
- Never render sensitive backend-only data on public pages.
- Apply strict dependency hygiene (lockfile, audit in CI).

---

## 14) SEO Strategy

- App Router metadata per page (title, description, canonical).
- Structured data (JSON-LD) for organization/site sections.
- Sitemaps + robots management.
- Fast TTFB and Core Web Vitals budgets.
- Content strategy emphasizing transparency and advisory boundaries.

---

## 15) Production Readiness Checklist

- [ ] TypeScript strict mode enabled and clean.
- [ ] Shared API envelope decoder implemented + tested.
- [ ] Public endpoint hooks with stale/retry policies documented.
- [ ] Global error/loading boundaries in App Router.
- [ ] Security headers/CSP validated in staging.
- [ ] A11y CI checks passing; manual QA sign-off complete.
- [ ] Vitest, contract tests, and Playwright pipelines green.
- [ ] Performance budgets enforced (LCP/CLS/INP).
- [ ] Observability wired (errors, web vitals, deployment markers).
- [ ] Canary + rollback playbook rehearsed.
- [ ] SEO artifacts (metadata/sitemap/robots) generated and validated.

---

## 16) Implementation Scope Note

This document is architecture-only and intentionally does **not** implement or refactor frontend code.
