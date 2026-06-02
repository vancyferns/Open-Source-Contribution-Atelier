# Contribution Proposal: Supabase-First Database Fallback to Neon

## Summary

This proposal adds a safe database fallback path for the backend so the application can continue working when Supabase is unavailable, while still keeping Supabase support in place for future use.

The intended behavior is:

1. Try the Supabase PostgreSQL connection first.
2. If Supabase cannot be reached, try the Neon PostgreSQL connection.
3. If neither cloud database is available, fall back to the existing local database setup used for development.

This keeps the project beginner-friendly, avoids removing existing infrastructure support, and reduces the chance that a regional outage or access issue prevents the app from starting.

## Problem

The repository currently supports cloud-hosted PostgreSQL-style environments, but a single unavailable provider can stop the application from starting or force contributors into manual recovery steps.

That creates two issues:

- Local contributors may be blocked when a preferred cloud database is unavailable.
- The project loses resilience even though it already has more than one viable PostgreSQL host option.

The goal of this change is not to remove Supabase. The goal is to make Supabase optional at runtime so the app can still run through Neon when Supabase is unreachable.

## Proposed Solution

Add a small database selection layer in the backend settings that evaluates cloud database URLs in order and picks the first reachable one.

### Selection order

1. `SUPABASE_DATABASE_URL`
2. `NEON_DATABASE_URL`
3. Existing local PostgreSQL env values, if configured
4. SQLite fallback for development when no external database is reachable

### Environment variables

Use the following variables in `backend/.env`:

- `SUPABASE_DATABASE_URL` for the primary cloud database
- `NEON_DATABASE_URL` for the fallback cloud database
- `DB_CONN_MAX_AGE` to keep persistent connection tuning explicit

### Runtime behavior

- The backend should not fail immediately when Supabase is down.
- The backend should not delete or disable Supabase configuration.
- The app should remain compatible with future scenarios where Supabase becomes reachable again.
- Existing auth and application logic should remain unchanged.

## Why This Approach

This approach is deliberately small and low-risk.

- It avoids a large architectural rewrite.
- It keeps the existing code paths intact.
- It preserves compatibility with local development and Docker-based workflows.
- It gives contributors a clear, testable fallback behavior instead of an implicit failure mode.

## Scope

### In scope

- Backend database configuration selection
- Environment variable documentation
- Tests for database selection order
- Minor README updates if needed

### Out of scope

- Replacing Supabase entirely
- Changing the auth flow
- Reworking frontend login behavior
- Migrating data between providers automatically
- Adding provider-specific dashboards or admin tooling

## Implementation Plan

### Step 1: Add a database selector helper

Create a small helper in the backend config layer that:

- reads Supabase and Neon URLs from environment variables
- checks whether each URL is reachable
- returns the first working PostgreSQL configuration
- falls back to the existing local configuration if both cloud options fail

### Step 2: Wire the helper into Django settings

Update `backend/config/settings.py` so the `DATABASES` setting uses the helper result.

### Step 3: Document the environment variables

Update `backend/.env.example` and the README so contributors know how to set:

- the Supabase URL
- the Neon URL
- the local fallback variables

### Step 4: Add tests

Add tests that verify:

- Supabase is selected when reachable
- Neon is selected when Supabase is unreachable
- local fallback still works when cloud databases are not configured

## Acceptance Criteria

The change is complete when all of the following are true:

- The backend can start when Supabase is unavailable, provided Neon is reachable.
- Supabase is still supported and remains the first cloud option.
- Neon is used automatically as the fallback cloud database.
- Existing local development behavior still works.
- The repository documents the new environment variables and startup expectation clearly.
- Tests cover the fallback order.

## Testing Plan

Recommended validation:

- `python manage.py check`
- `python -m pytest tests/test_database_configuration.py`
- `python manage.py migrate`
- `python manage.py runserver`

If the environment uses a restricted network, contributors should be told to trust the repo’s pinned package versions or use the provided Docker path.

## Alternatives Considered

### 1. Remove Supabase support entirely

Rejected because the project explicitly should not remove Supabase.

### 2. Require manual switching in `.env`

Rejected because it puts the burden on contributors and breaks the goal of automatic fallback.

### 3. Add complex failover logic with retries, pools, and provider health checks

Rejected because the project needs a simple and maintainable fallback, not a distributed systems layer.

## Risks And Mitigations

### Risk: false-positive connectivity checks

Mitigation: keep the check simple and test the exact URLs in order.

### Risk: developer confusion about which database is active

Mitigation: document the selection order in the README and `.env.example`.

### Risk: accidental regression in local development

Mitigation: preserve the existing local config and cover it with tests.

## Contributor Checklist

- [ ] Keep Supabase support intact
- [ ] Add Neon fallback behavior
- [ ] Update env documentation
- [ ] Add tests for fallback order
- [ ] Run backend checks locally
- [ ] Confirm no secrets are committed

## Suggested Branch Name

`feature/supabase-neon-fallback`

## Suggested Issue Title

`feat: add Supabase-first Neon fallback for backend database`

## Notes For Reviewers

This proposal is intentionally focused on reliability and contributor experience. It keeps the existing architecture recognizable, minimizes risk, and gives maintainers a clear fallback path without removing any supported provider.