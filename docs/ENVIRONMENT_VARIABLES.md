# Environment Variables

This repository uses environment-driven configuration; never commit real secrets.

## Core backend
- `APP_ENV` (dev/staging/production)
- `DEBUG` (`true`/`false`)
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`

## Frontend
- `NEXT_PUBLIC_API_BASE_URL` (public-safe base URL only)

## Notes
- Production should inject secrets from external secure tooling.
- `.env.example` must contain placeholders only.
