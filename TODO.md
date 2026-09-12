# TODO — QuickFix Nearby

Tracking build-out of the marketplace described in `README.md`. Check items off as they land on `main`.

## Phase 1 — Foundation
- [x] Flask app factory (`app/__init__.py`)
- [x] SQLAlchemy wired up — SQLite by default (`instance/quickfix.db`), swaps to Neon Postgres automatically when `DATABASE_URL` is set
- [ ] Verify against a real Neon Postgres database (only tested against SQLite so far)
- [ ] Flask-Migrate / Alembic wired up — `db.create_all()` is a dev-only stopgap right now
- [x] `requirements.txt`
- [x] `.env.example` (no real secrets, ever)
- [x] `vercel.json` routing requests to the Flask WSGI app — scaffolded, not yet verified against a real deploy

## Phase 2 — Data models
- [x] `users` — id, name, email, password_hash, role, service_category, verified, created_at, updated_at
- [ ] Split professional-only fields (`service_category`, `verified`) into a dedicated `professionals` table with coverage_area, rating, total_jobs, etc., per README's data model
- [ ] `customers` — id, user_id, phone, location
- [ ] `service_requests` — id, customer_id, professional_id, service_type, description, location, urgency, status, created_at
- [x] `contact_submissions` — landing-page leads, now persisted via `/leads` and surfaced on professional/admin dashboards

## Phase 3 — Auth
- [x] Email/password signup + login with hashed passwords (Werkzeug)
- [ ] Google OAuth flow
- [x] Session management (Flask-Login)
- [ ] CSRF protection on every form (Flask-WTF) — including `/leads`, `/login`, `/register`
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
- [ ] Move `app/static/css/style.css` into a Tailwind build pipeline (currently hand-rolled CSS for the MVP)
- [ ] PWA manifest + service worker

## Phase 8 — AI/ML
- [ ] Hugging Face integration — e.g. auto-categorizing free-text job descriptions

## Phase 9 — Security & hardening
- [ ] Security headers: CSP, X-Frame-Options, X-Content-Type-Options
- [ ] Rate limiting on auth endpoints and `/leads`
- [ ] CSRF protection (see Phase 3)
- [ ] Input validation on every form and API route

## Phase 10 — Deployment
- [ ] Vercel project + env vars set (Production and Preview)
- [ ] Confirm `vercel.json` routing works against a real deploy (static assets + SQLite won't persist on serverless — Postgres is required before deploying)
- [ ] Production Neon database provisioned
- [ ] Post-deploy smoke test
- [ ] Basic monitoring / error tracking

## Housekeeping
- [x] Add `app/static/logo.png` — uploaded and wired into nav, footer, and favicon
- [ ] Replace placeholder stats and testimonial on the landing page with real numbers before launch
- [ ] Add `LICENSE` file (README references MIT)
- [ ] Rotate any credentials that were ever pasted outside `.env`
