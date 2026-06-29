# Bitcoin Bastion Repository Style Guide

This style guide defines conventions for organizing code, documentation and interfaces across the `bitcoinbastion` repository.  It aims to make the codebase easy to navigate for new contributors, to clearly separate backend and frontend concerns, and to ensure that all documentation is consistent, complete and aligned with the project’s design philosophy.

## Repository layout

The repository contains multiple subsystems.  To make the structure more intuitive, adhere to the following conventions:

### Backend

The backend codebase lives primarily in the `app/` directory and supports FastAPI services, Celery workers, database migrations and core business logic.  Related directories include:

- `app/` – Python packages implementing services, models, tasks and API routes.  The **services** directory houses domain‐specific services such as bastion trace, citadel, market data, mempool, treasury and intelligence【turn52file0†L18-L48】【turn66file0†L39-L70】.  Each subpackage should expose a clear public API and publish domain events through the event bus【turn58file0†L61-L136】.
- `app/db/` – SQLAlchemy models, Alembic migrations and seeds.  New migrations should follow the naming pattern `YYYYMMDD_HHmm_description.py` and include upgrade and downgrade logic.  Migrations must be idempotent and accompanied by migration smoke tests.
- `deploy/` – Kubernetes manifests and Helm charts for running the backend in production.  All changes require updating `docs/PRODUCTION_READINESS.md` with new evidence collection steps.
- `tests/` – Pytest suites for unit and integration tests.  New features must include tests and use the existing fixtures.

### Frontend

There are currently three frontend surfaces:

- `app/web/` – FastAPI + Jinja templates used for lightweight pages such as status dashboards and health probes.  They remain supported until Reflex covers their routes【turn76file0†L11-L25】.
- `reflex_frontend/` – the Python-first frontend built on the Reflex framework. New user-facing functionality should be added here.  Refer to `docs/FRONTEND_REFLEX_MIGRATION_BASELINE.md` for the baseline inventory【turn76file0†L11-L25】 and `reflex_frontend/docs/DESIGN_SYSTEM.md` for design principles【turn84file0†L5-L17】.

The old frontend has been removed; do **not** reintroduce it. Do not remove `app/web/` Market routes without a separate ownership plan.

## Documentation conventions

Every new subsystem, service or feature must be accompanied by documentation in the `docs/` directory.  Documentation should follow a consistent structure:

1. **Title and overview** – A brief description of the subsystem’s purpose and scope.
2. **Architecture** – High‑level design and key components, with diagrams where helpful.  Describe how the subsystem interacts with the event bus and other services.
3. **Endpoints / routes / APIs** – For backend modules, list REST endpoints and expected request/response schemas.  For frontend modules, list routes and the backend endpoints they consume【turn74file0†L6-L19】.
4. **Data models** – Describe database tables or objects created by the subsystem.  Include schema diagrams and migration references when appropriate【turn85file0†L19-L31】.
5. **Safety copy and limitations** – Explain how the subsystem enforces the project’s no‑custody posture, how degraded or fallback states are surfaced to users, and any known limitations or side‑effects【turn82file0†L26-L38】.
6. **Status and roadmap** – Indicate whether the subsystem is production‑ready, experimental or incomplete.  Document any outstanding tasks, parity gaps or deferred work【turn78file0†L134-L144】.

When adding new documentation:

- Use descriptive file names (`HISTORICAL_SIMILARITY_ENGINE.md`, `FRONTEND_REFLEX_MARKET_TIME_MACHINE.md`, etc.) and avoid abbreviations.
- Link related documents using relative paths and mention them in the **Core documentation** section of the README.
- Include citations to code or migration files where appropriate to make cross‑references easy for reviewers.

### Frontend doc style

Docs describing frontend pages (Reflex and any delegated Jinja surfaces) should list the route(s), the backend endpoint(s) they depend on, and the safety copy and degraded‑state handling.  They should also note any missing endpoints or gaps to parity【turn74file0†L6-L19】.  The `docs/FRONTEND_REFLEX_MIGRATION_BASELINE.md` file provides an inventory of routes and should be updated as new pages are added.

### Migration docs

When database migrations add new tables or columns or seed data, include a corresponding doc (or update an existing doc) explaining the purpose of the tables, the data seeded, and how the new models integrate into the system.  For example, migrations adding `source_health_records` and expanding `market_pattern_library` are documented in the **ongoing work** section of the README【turn85file0†L19-L31】【turn86file0†L41-L76】.

## Code style guidelines

- **Python version** – Target Python 3.12 or later; avoid deprecated syntax.
- **Formatting** – Use [Black](https://github.com/psf/black) or the repository’s configured formatter to enforce consistent whitespace, line length and quoting.  Run `make lint` before committing.
- **Type hints** – Add type annotations to function arguments and return types.  Use `typing.Optional` and `typing.Dict` where appropriate.  Keep type hints simple and avoid unnecessary generics.
- **Docstrings** – Use [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) or NumPy docstring conventions.  The first line should be a short summary; subsequent paragraphs may describe parameters, return types and exceptions.
- **Naming conventions** – Use snake_case for functions and variables, PascalCase for classes, and SCREAMING_SNAKE_CASE for constants.  Avoid abbreviations and overly terse names.
- **Tests** – All new features must include unit tests under `tests/` or extend existing integration tests.  Tests should cover normal and error conditions.

## Contribution guidelines

- Before submitting a pull request, run `make lint`, `pytest` and the CI gates (`make ci-release-gates`).  Fix any failing tests or lint errors.
- Update relevant documentation and the README when adding new functionality or modifying existing behavior.  The README’s **Ongoing work and future modules** section should be updated when new migrations or engines are introduced.
- Respect the **no‑custody** and **operator control** principles: never request, store or expose private keys, seed phrases or secrets【turn1file0†L160-L167】.  Risky actions must require explicit operator approval.
- Maintain evidence: new features that impact production readiness must include automated evidence generation (e.g., migration smoke tests) and updates to the **PRODUCTION_READINESS** docs.

## Separating backend and frontend documentation

To reduce confusion between backend services and frontend user interfaces, create subfolders within `docs/`:

- `docs/backend/` – houses docs for backend subsystems (e.g., Historical Similarity Engine, Market Signal Governance, Evidence Packets).  These should focus on APIs, data models and internal logic.
- `docs/frontend/` – historical UI planning docs; current frontend implementation lives in `reflex_frontend/`.  Each file should correspond to a page or group of pages and include routes, backend dependencies, safety copy and state handling.

Existing docs can be moved into these subfolders over time.  When moving files, ensure all links in other docs and the README are updated accordingly.

---

By adhering to this style guide, contributors can keep the repository organised and coherent while the project continues to evolve.  Clear separation between backend and frontend code, consistent documentation conventions and strong coding standards will make the Bitcoin Bastion codebase easier to understand, safer to extend and faster to review.
