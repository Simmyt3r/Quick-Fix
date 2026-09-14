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
- [x] Cloudinary credentials added to Vercel env vars (`CLOUDINARY_CLOUD_NAME`/`API_KEY`/`API_SECRET`) — wired up in `app/uploads.py`, currently used for profile photos

## Phase 2 — Data models
- [x] `users` — id, name, email, password_hash, role, service_category, verified, created_at, updated_at
- [ ] Split professional-only fields (`service_category`, `verified`) into a dedicated `professionals` table with coverage_area, rating, total_jobs, etc., per README's data model
- [ ] `customers` — id, user_id, phone, location
- [x] `service_requests` — id, customer_id, professional_id, category, description, location, urgency, status, created_at, updated_at — live, with FK relationships to `users` for both customer and professional
- [x] `contact_submissions` — landing-page leads, persisted via `/leads` and surfaced on professional/admin dashboards
- [x] `users.avatar_url` — Cloudinary-hosted profile photo, nullable (falls back to an initial-letter avatar in the UI)

## Phase 3 — Auth
- [x] Email/password signup + login with hashed passwords (Werkzeug)
- [x] Google OAuth flow (Authlib + OIDC) — links to an existing password account by verified email if one matches, otherwise creates a new customer-role account; app runs fine without `GOOGLE_CLIENT_ID`/`SECRET` set, the button just doesn't render. No mid-flow "pick your role" step yet, so Google sign-ups always land as customer — see the note on the register page
- [x] Session management (Flask-Login)
- [x] CSRF protection on every form (Flask-WTF) — `/leads`, `/login`, `/register` all require a valid token; failures flash a friendly message and redirect
- [ ] Password reset flow
- [x] Open-redirect protection on the post-login `next` param

## Phase 4 — Customer experience
- [x] Dashboard: request form (category, description, location, urgency) posting to `/requests/new`
- [x] Service-request status tracking — customer sees pending/accepted/completed/cancelled on their dashboard
- [x] Customer can cancel their own pending request (`/requests/<id>/cancel`) — only while still pending, only their own
- [ ] Post-job rating & review

## Phase 5 — Professional experience
- [x] Basic dashboard — profile card (trade + verification badge), open requests in trade, active/completed jobs, and matching leads
- [x] Incoming request accept/decline — `/requests/<id>/accept` (scoped to matching category, first-to-accept wins), `/requests/<id>/complete`. No decline action yet (a pro just leaves it for someone else)
- [ ] Full profile setup — coverage area, availability toggle
- [ ] Identity/verification doc upload (Cloudinary) — the Cloudinary plumbing now exists (`app/uploads.py`, used for profile photos), so this is mostly a matter of a second upload flow + admin review UI, not new infrastructure
- [ ] Earnings + job history dashboard (jobs list exists; no earnings/payment tracking yet)

## Phase 6 — Admin
- [x] Basic dashboard — user/lead/service-request counts, recent leads table, recent service requests table (with customer + assigned professional names)
- [x] `flask create-admin` CLI command (no public admin signup)
- [ ] Provider approval / verification review queue (flip `verified` from the dashboard instead of the DB directly) — note: `verified` currently isn't enforced anywhere, an unverified pro can still accept jobs
- [ ] Incident tracking
- [ ] Full reporting dashboard

## Phase 7 — Frontend
- [x] Marketing landing page (`app/templates/index.html`), served via Flask (`GET /`)
- [x] Auth pages (`/login`, `/register`) and role-aware dashboard (`/dashboard`)
- [x] Global `<meta name="csrf-token">` on authenticated pages, independent of whether a form happens to render (dashboard pages with empty tables previously had nowhere to source a token from for JS/testing)
- [x] Applied the blue/green/white brand palette to `app/static/css/style.css` (screenshot-tested at desktop + mobile widths; fixed a blue-on-blue button and a flex-gap fallback along the way)
- [x] PWA manifest + service worker, mobile tile-grid dashboard, bottom nav (Home / Request / Log out)
- [x] Slide-out sidebar (mobile drawer, hamburger-triggered) with Home/Profile/Settings/Log out — on desktop (≥641px) it becomes a persistent rail, which also fixes a real gap: authenticated desktop users previously had no navigation at all once the bottom-nav hides at that width
- [x] Profile page (`/profile/`) — edit name, upload a profile photo (Cloudinary), and (for professionals) trade category + verification status
- [x] Settings page (`/profile/settings`) — change password, with a graceful message for Google-only accounts that have none
- [ ] Move `app/static/css/style.css` into a Tailwind build pipeline (currently hand-rolled CSS for the MVP)

## Phase 8 — AI/ML
- [ ] Hugging Face integration — e.g. auto-categorizing free-text job descriptions

## Phase 9 — Security & hardening
- [x] Security headers: CSP (no `unsafe-inline`), X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS (HTTPS only) — `img-src` extended to allow `res.cloudinary.com` for avatar images
- [x] Rate limiting on `/login` (10/min), `/register` (5/hr), `/leads` (10/hr) via Flask-Limiter — **in-memory storage only, resets per process; not safe for multiple serverless instances (see Phase 10)**
- [ ] Input validation on every form and API route

## Phase 10 — Deployment
- [x] Fixed a crash-on-every-request bug: `create_app()` was unconditionally calling `os.makedirs()` for the SQLite fallback, even when `DATABASE_URL` was set — Vercel's serverless filesystem is read-only outside `/tmp`, so this crashed the function on every invocation. Now it only touches the filesystem when actually falling back to SQLite, and fails with a clear message (not a cryptic OSError) if `DATABASE_URL` is missing on Vercel.
- [x] Neon project provisioned, `DATABASE_URL` set in Vercel — site is live at quickfixnearby.vercel.app
- [x] Vercel project + env vars set (Production) — confirmed live; double check Preview env vars are set too if preview deploys are used
- [x] Confirm `vercel.json` routing works against a real deploy (static assets) — confirmed: logo and styling load correctly on the live homepage
- [x] Decided how migrations run in production — `.github/workflows/migrate.yml`, manually triggered (`workflow_dispatch`) against a `DATABASE_URL` repo secret. First run failed, second succeeded (2026-09-13) — **worth glancing at the failed run's logs once to understand why, so it doesn't repeat on the next schema change**
- [ ] **Confirm the GitHub Actions `DATABASE_URL` secret and the Vercel `DATABASE_URL` env var point at the same Neon database** — if they don't, the app will boot fine but registration/login will fail with a "relation does not exist" error even though the homepage loads
- [ ] Full post-deploy smoke test — homepage confirmed rendering correctly; **still needs someone to actually register an account, log in, and load the dashboard on the live site** to confirm the DB write path works end-to-end (I can't do this remotely without live credentials)
- [ ] Replace Flask-Limiter's in-memory storage with a shared backend (e.g. Upstash Redis) before relying on rate limits in production — each serverless instance currently tracks its own counters
- [ ] Basic monitoring / error tracking

## Housekeeping
- [x] `app/static/logo.png` — uploaded and wired into nav, footer, and favicon
- [ ] Replace placeholder stats and testimonial on the landing page with real numbers before launch
- [ ] Add `LICENSE` file (README references MIT)
- [ ] Rotate any credentials that were ever pasted outside `.env`
