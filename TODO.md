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
- [x] `users` — id, name, email, password_hash, is_customer, is_professional, role (admin-only flag now — see below), service_category, verified, disabled, reset_token, reset_token_expires, created_at, updated_at — **role migrated from a single customer/professional/admin string to two independent booleans, `is_customer` and `is_professional`, so an account can be both at once; `role` is kept solely to flag admins (2026-09-15, migration `b159fdb92b59`)**. `disabled` added 2026-09-17 (migration `c3097a33c5be`) — an admin-managed account-status flag, enforced at login and mid-session (see Phase 6). `reset_token`/`reset_token_expires` added 2026-09-17 (migration `236021afdff7`) — see Phase 3.
- [ ] Split professional-only fields (`service_category`, `verified`) into a dedicated `professionals` table with coverage_area, rating, total_jobs, etc., per README's data model
- [ ] `customers` — id, user_id, phone, location
- [x] `service_requests` — id, customer_id, professional_id, category, description, location, urgency, status, created_at, updated_at — live, with FK relationships to `users` for both customer and professional
- [x] `contact_submissions` — landing-page leads, persisted via `/leads` and surfaced on professional/admin dashboards
- [x] `users.avatar_url` — Cloudinary-hosted profile photo, nullable (falls back to an initial-letter avatar in the UI)
- [x] `incidents` — id, reported_by_id, subject_user_id, service_request_id, category, note, status, created_at, resolved_at (2026-09-17, migration `c3097a33c5be`) — see Phase 6
- [x] `admin_actions` — id, admin_id, action, target_user_id, target_incident_id, detail, created_at (2026-09-17, migration `c3097a33c5be`) — audit trail, see Phase 6
- [x] `reviews` — id, service_request_id (unique), customer_id, professional_id, rating, comment, created_at (2026-09-18, migration `063cbb7fd9bd`) — see Phase 4
- [x] `service_requests.requested_professional_id` — nullable FK to `users`, set when a customer books via a professional's public profile rather than open category-matching (2026-09-19, migration `4b45a5d9543a`) — see Phase 5

## Phase 3 — Auth
- [x] Email/password signup + login with hashed passwords (Werkzeug)
- [x] Google OAuth flow (Authlib + OIDC) — links to an existing password account by verified email if one matches, otherwise creates a new customer-only account; app runs fine without `GOOGLE_CLIENT_ID`/`SECRET` set, the button just doesn't render. No mid-flow "pick your role" step, so Google sign-ups always land as customer-only — but any account (Google or password) can add the professional role afterwards from Profile Settings, since account type is now two independent flags rather than one fixed role (see Phase 2)
- [x] Session management (Flask-Login)
- [x] CSRF protection on every form (Flask-WTF) — `/leads`, `/login`, `/register` all require a valid token; failures flash a friendly message and redirect
- [x] Password reset flow — `/forgot-password` and `/reset-password/<token>` via Gmail SMTP (`app/mail.py`). Same-message-either-way to avoid account enumeration; Google-only accounts get an explanatory email instead of a broken link; disabled accounts get nothing. Token is a random string on the user row (not a signed JWT), genuinely single-use, 1-hour expiry. Migration `236021afdff7`. SMTP env vars added to Vercel 2026-09-17 — **not yet confirmed a real email actually arrived; the flow degrades gracefully (logs the link server-side) if they're missing or wrong, so a silent misconfiguration wouldn't show up as an error**
- [x] Open-redirect protection on the post-login `next` param

## Phase 4 — Customer experience
- [x] Dashboard: request form (category, description, location, urgency) posting to `/requests/new`
- [x] Service-request status tracking — customer sees pending/accepted/completed/cancelled on their dashboard
- [x] Customer can cancel their own pending request (`/requests/<id>/cancel`) — only while still pending, only their own
- [x] Post-job rating & review — customer rates a completed job 1–5 stars with an optional comment (`Review` model, migration `063cbb7fd9bd`). One review per service request (enforced with a DB unique constraint on `service_request_id`, and in the route). Customer-to-professional only for now — **assumption, not explicitly confirmed**; a reverse direction later just needs a `direction` column, not a new table. A completed-and-unreviewed job shows a "Rate this job" prompt with a CSS-only star picker on the customer's dashboard; a reviewed job shows the stars given instead. A professional's average rating is now visible on the public directory/profile pages (see Phase 5) before a customer books them. Still open: no reply-to-review; no flag/report review flow.

## Phase 5 — Professional experience
- [x] Basic dashboard — profile card (trade + verification badge), open requests in trade, active/completed jobs, and matching leads
- [x] Incoming request accept/decline — `/requests/<id>/accept` (scoped to matching category, first-to-accept wins), `/requests/<id>/complete`. No decline action yet (a pro just leaves it for someone else)
- [x] Public professional directory & profile pages — `/pros/` (browsable, filterable by category, verified professionals only) and `/pros/<id>` (avatar, trade, average rating, up to 20 recent reviews). Unauthenticated — a 404 for unverified/disabled/nonexistent pros rather than a redirect, since this is a plain content page someone might hit via a shared link. "Find a pro" linked from the marketing nav, the landing page, and the logged-in sidebar (customers only). Migration `4b45a5d9543a` (2026-09-19).
- [x] Targeted booking ("Request this pro") — booking via a profile page sets `ServiceRequest.requested_professional_id`; the request form locks to that pro's trade, and only they (not any other pro in the same category) can see or accept it. The normal open/category-matched flow is unaffected.
- [ ] Full profile setup — coverage area, availability toggle
- [ ] Identity/verification doc upload (Cloudinary) — the Cloudinary plumbing now exists (`app/uploads.py`, used for profile photos), so this is mostly a matter of a second upload flow + admin review UI, not new infrastructure
- [ ] Earnings + job history dashboard (jobs list exists; no earnings/payment tracking yet)

## Phase 6 — Admin
- [x] Basic dashboard — user/lead/service-request counts, recent leads table, recent service requests table (with customer + assigned professional names); admin dashboard now also has quick-action tiles (Verification / Users / Incidents / Activity log) with live pending-verification and open-incident counts
- [x] `flask create-admin` CLI command (no public admin signup) — promotes an existing account to admin in place if the email is already registered (password untouched), rather than silently no-op'ing; three distinct outcome messages (created / promoted / already admin) so a GitHub Actions run's "success" status can't mask which branch actually ran (2026-09-19, after this exact ambiguity caused a real mix-up promoting Simmy's own account)
- [x] Provider approval / verification review queue — `/admin/verification`, approve/reject with an optional reason. `verified` is now actually enforced: `requests.py` blocks an unverified professional from accepting a job (2026-09-17, migration `c3097a33c5be`)
- [x] User management — `/admin/users`: search by name/email, filter by role and status, disable/re-enable accounts. A disabled user is blocked at both login paths (password and Google) and their *existing* session is killed on the next request (via the `user_loader` hook returning `None`), not just blocked at login. Admins can't disable themselves or other admins from this screen.
- [x] Incident tracking — `/admin/incidents`, `/admin/incidents/new`: a report (category: no-show / dispute / complaint / other, a note, open/resolved status) attachable to a user and/or a service request. Linkable from the users list ("Log incident" on any row). No public report form yet — admins log these directly, not customers/professionals themselves.
- [x] Admin action audit log — `/admin/activity`: every admin action above (verify, reject, disable, enable, log incident, resolve incident) is recorded automatically via a `log_action()` helper — who did what, to whom, when
- [ ] Full reporting dashboard beyond the counts/tiles above (e.g. trends over time, exportable data) — the basics (counts, recent activity, filterable user list) now exist; this item is for anything beyond that

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
- [x] Swept every template for inline `<script>`/`style=""`/`on*=` attributes that the strict CSP would silently block — found and fixed one real case (service-worker registration script + two inline `style=""` attributes in `base_app.html`/`dashboard.html`/`profile/view.html`), moved to external `.js` files and CSS classes (2026-09-15)
- [x] Fixed Service Worker registration `SecurityError` (scope `/` not allowed under `/static/`) — `vercel.json`'s top-level `headers` block was unreliable when mixed with the legacy `builds`+`routes` config, so `Service-Worker-Allowed: /` is now set both route-level in `vercel.json` and directly from Flask (`app/security.py`, scoped to exactly `/static/sw.js`) as a guaranteed fallback (2026-09-19)
- [x] Rate limiting on `/login` (10/min), `/register` (5/hr), `/leads` (10/hr) via Flask-Limiter — **in-memory storage only, resets per process; not safe for multiple serverless instances (see Phase 10)**
- [ ] Input validation on every form and API route

## Phase 10 — Deployment
- [x] Fixed a crash-on-every-request bug: `create_app()` was unconditionally calling `os.makedirs()` for the SQLite fallback, even when `DATABASE_URL` was set — Vercel's serverless filesystem is read-only outside `/tmp`, so this crashed the function on every invocation. Now it only touches the filesystem when actually falling back to SQLite, and fails with a clear message (not a cryptic OSError) if `DATABASE_URL` is missing on Vercel.
- [x] Neon project provisioned, `DATABASE_URL` set in Vercel — site is live at quickfixnearby.vercel.app
- [x] Vercel project + env vars set (Production) — confirmed live; double check Preview env vars are set too if preview deploys are used
- [x] Confirm `vercel.json` routing works against a real deploy (static assets) — confirmed: logo and styling load correctly on the live homepage
- [x] Decided how migrations run in production — `.github/workflows/migrate.yml`, manually triggered (`workflow_dispatch`) against a `DATABASE_URL` repo secret. First run failed, second succeeded (2026-09-13) — **worth glancing at the failed run's logs once to understand why, so it doesn't repeat on the next schema change**
- [x] `.github/workflows/create-admin.yml` — same manually-triggered pattern as migrate.yml, wraps `flask create-admin` so an admin account can be created (or an existing account promoted) against production without local `DATABASE_URL` access or a shell on the host. Password is passed as a plain `workflow_dispatch` input, so it's visible in the run log — accepted tradeoff for a private repo (2026-09-19)
- [x] **Confirm the GitHub Actions `DATABASE_URL` secret and the Vercel `DATABASE_URL` env var point at the same Neon database** — ✅ confirmed indirectly: registration on the live site succeeds (would fail with "relation does not exist" if they pointed at different databases), and 0 errors in Vercel runtime logs during the test window (2026-09-16)
- [x] Full post-deploy smoke test — confirmed end-to-end on the live site (2026-09-16): registered a real account choosing both the customer and professional roles (dual-role account), login and dashboard both worked, 0 errors in Vercel runtime logs during the window
- [x] Admin features migration (`c3097a33c5be`) applied to production and verified clean — triggered `migrate.yml` immediately after the push, polled to completion, confirmed 0 errors in Vercel runtime logs and a healthy homepage fetch afterward (2026-09-17). This is now the standing practice for every schema-changing push, not a one-off.
- [ ] Replace Flask-Limiter's in-memory storage with a shared backend (e.g. Upstash Redis) before relying on rate limits in production — each serverless instance currently tracks its own counters
- [ ] Basic monitoring / error tracking

## Housekeeping
- [x] `app/static/logo.png` — uploaded and wired into nav, footer, and favicon
- [ ] Replace placeholder stats and testimonial on the landing page with real numbers before launch
- [x] Add `LICENSE` file (README references MIT) — added, copyright attributed to Simeon's Laboratories and Co Technologies Ltd (Silabs) as an assumption based on the company being the one building this; flag if that's wrong and it needs a different holder
- [ ] Rotate any credentials that were ever pasted outside `.env`. Confirmed exposed, from this session's own record: the GitHub PAT (`github_pat_11BJ6...`), pasted directly into chat multiple times across sessions and used repeatedly for pushes and workflow dispatches — **rotate this one specifically, it's the one I'm certain about**. I don't have visibility into earlier sessions, so I can't confirm or rule out whether `DATABASE_URL` (Neon), `GOOGLE_CLIENT_SECRET`, `CLOUDINARY_URL`, or `SMTP_PASSWORD` were ever pasted in chat before this — worth a quick personal check of your own conversation history for any of those before considering this item done
