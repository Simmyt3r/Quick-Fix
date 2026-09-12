# TODO — QuickFix Nearby

Tracking build-out of the marketplace described in `README.md`. Check items off as they land on `main`.

## Phase 1 — Foundation
- [x] Flask app factory (`app/__init__.py`)
- [x] SQLAlchemy wired up — SQLite by default (`instance/quickfix.db`), swaps to Postgres automatically when `DATABASE_URL` is set (normalizes `postgres://` → `postgresql://`)
- [x] Flask-Migrate / Alembic wired up — `migrations/` is committed; run `flask db upgrade` to create/update schema (replaces the old `db.create_all()` dev stopgap)
- [x] Verified migrations against a real local Postgres 16 instance (tables created, full auth/dashboard smoke test passed) — **not yet verified against actual Neon**, since that needs your real connection string
- [x] `requirements.txt`
- [x] `.env.example` (no real secrets, ever)
- [x] `vercel.json` routing requests to the Flask WSGI app — scaffolded, not yet verified against a real deploy

## Phase 2 — Data models
- [x] `users` — id, name, email, password_hash, role, service_category, verified, created_at, updated_at
- [ ] Split professional-only fields (`service_category`, `verified`) into a dedicated `professionals` table with coverage_area, rating, total_jobs, etc., per README's data model
- [ ] `customers` — id, user_id, phone, location
- [ ] `service_requests` — id, customer_id, professional_id, service_type, description, location, urgency, status, created_at
- [x] `contact_submissions` — landing-page leads, persisted via `/leads` and surfaced on professional/admin dashboards

## Phase 3 — Auth
- [x] Email/password signup + login with hashed passwords (Werkzeug)
- [x] Google OAuth flow (Authlib + OIDC) — links to an existing password account by verified email if one matches, otherwise creates a new customer-role account; app runs fine without `GOOGLE_CLIENT_ID`/`SECRET` set, the button just doesn't render. No mid-flow "pick your role" step yet, so Google sign-ups always land as customer — see the note on the register page
- [x] Session management (Flask-Login)
- [x] CSRF protection on every form (Flask-WTF) — `/leads`, `/login`, `/register` all require a valid token; failures flash a friendly message and redirect
- [ ] Password reset flow
- [x] Open-redirect protection on the post-login `next` param

## Phase 4 — Customer experience
- [x] Basic dashboard (empty-state placeholder for requests)
- [ ] Service request form (category, location, urgency, schedule)
- [ ] Booking/service-request status tracking
- [ ] Post-job rating & review

## Phase 5 — Professional experience
- [x] Basic dashboard — profile card (trade + verification badge) and matching leads list
- [ ] Full profile setup — coverage area, availability toggle
- [ ] Identity/verification doc upload (Cloudinary)
- [ ] Incoming request accept/decline
- [ ] Earnings + job history dashboard

## Phase 6 — Admin
- [x] Basic dashboard — user/lead counts + recent leads table
- [x] `flask create-admin` CLI command (no public admin signup)
- [ ] Provider approval / verification review queue (flip `verified` from the dashboard instead of the DB directly)
- [ ] Incident tracking
- [ ] Full reporting dashboard

## Phase 7 — Frontend
- [x] Marketing landing page (`app/templates/index.html`), served via Flask (`GET /`)
- [x] Auth pages (`/login`, `/register`) and role-aware dashboard (`/dashboard`)
- [x] Applied the blue/green/white brand palette to `app/static/css/style.css` (screenshot-tested at desktop + mobile widths; fixed a blue-on-blue button and a flex-gap fallback along the way)
- [ ] Move `app/static/css/style.css` into a Tailwind build pipeline (currently hand-rolled CSS for the MVP)
- [ ] PWA manifest + service worker

## Phase 8 — AI/ML
- [ ] Hugging Face integration — e.g. auto-categorizing free-text job descriptions

## Phase 9 — Security & hardening
- [x] Security headers: CSP (no `unsafe-inline`), X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS (HTTPS only)
- [x] Rate limiting on `/login` (10/min), `/register` (5/hr), `/leads` (10/hr) via Flask-Limiter — **in-memory storage only, resets per process; not safe for multiple serverless instances (see Phase 10)**
- [ ] Input validation on every form and API route

## Phase 10 — Deployment
- [x] Fixed a crash-on-every-request bug: `create_app()` was unconditionally calling `os.makedirs()` for the SQLite fallback, even when `DATABASE_URL` was set — Vercel's serverless filesystem is read-only outside `/tmp`, so this crashed the function on every invocation. Now it only touches the filesystem when actually falling back to SQLite, and fails with a clear message (not a cryptic OSError) if `DATABASE_URL` is missing on Vercel.
- [ ] Provision a real Neon project, put its connection string in `DATABASE_URL` (locally and in Vercel's env vars), then run `flask db upgrade` against it once from a machine that can reach it
- [ ] Vercel project + env vars set (Production and Preview)
- [ ] Confirm `vercel.json` routing works against a real deploy (static assets)
- [ ] Replace Flask-Limiter's in-memory storage with a shared backend (e.g. Upstash Redis) before relying on rate limits in production — each serverless instance currently tracks its own counters
- [ ] Decide how migrations run in production (Vercel serverless functions shouldn't run `flask db upgrade` on cold start — run it manually or from CI before each deploy)
- [ ] Post-deploy smoke test
- [ ] Basic monitoring / error tracking

## Housekeeping
- [x] `app/static/logo.png` — uploaded and wired into nav, footer, and favicon
- [ ] Replace placeholder stats and testimonial on the landing page with real numbers before launch
- [ ] Add `LICENSE` file (README references MIT)
- [ ] Rotate any credentials that were ever pasted outside `.env`
