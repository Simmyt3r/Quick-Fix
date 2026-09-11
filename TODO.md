# TODO — QuickFix Nearby

Tracking build-out of the marketplace described in `README.md`. Check items off as they land on `main`.

## Phase 1 — Foundation
- [x] Flask app factory (`app/__init__.py`)
- [ ] Neon Postgres connection + SQLAlchemy setup
- [ ] Flask-Migrate / Alembic wired up
- [x] `requirements.txt`
- [x] `.env.example` (no real secrets, ever)
- [x] `vercel.json` routing requests to the Flask WSGI app — scaffolded, not yet verified against a real deploy

## Phase 2 — Data models
- [ ] `users` — id, name, email, password_hash, role, google_id, profile_picture, created_at, updated_at
- [ ] `customers` — id, user_id, phone, location
- [ ] `professionals` — id, user_id, service_type, verified, rating, total_jobs, coverage_area
- [ ] `service_requests` — id, customer_id, professional_id, service_type, description, location, urgency, status, created_at
- [ ] `contact_submissions` — landing-page leads (the `/leads` route currently just logs; wire it to this table)

## Phase 3 — Auth
- [ ] Email/password signup + login with hashed passwords
- [ ] Google OAuth flow
- [ ] Flask session management
- [ ] CSRF protection on every form (Flask-WTF) — including the public `/leads` form

## Phase 4 — Customer experience
- [ ] Service request form (category, location, urgency, schedule)
- [ ] Booking/service-request status tracking
- [ ] Post-job rating & review

## Phase 5 — Professional experience
- [ ] Profile setup — service type, coverage area, availability
- [ ] Identity/verification doc upload (Cloudinary)
- [ ] Incoming request accept/decline
- [ ] Earnings + job history dashboard

## Phase 6 — Admin
- [ ] Provider approval / verification review queue
- [ ] Incident tracking
- [ ] Reporting dashboard
- [ ] Contact-submission (lead) management

## Phase 7 — Frontend
- [x] Marketing landing page (`app/templates/index.html`), served via Flask (`GET /`)
- [ ] Jinja2 templates for authenticated app views
- [ ] Move `app/static/css/style.css` into a Tailwind build pipeline (currently hand-rolled CSS for the MVP)
- [ ] PWA manifest + service worker

## Phase 8 — AI/ML
- [ ] Hugging Face integration — e.g. auto-categorizing free-text job descriptions

## Phase 9 — Security & hardening
- [ ] Security headers: CSP, X-Frame-Options, X-Content-Type-Options
- [ ] Rate limiting on auth endpoints (and on `/leads`)
- [ ] Input validation on every form and API route

## Phase 10 — Deployment
- [ ] Vercel project + env vars set (Production and Preview)
- [ ] Confirm `vercel.json` routing works against a real deploy (static assets under `app/static/`)
- [ ] Production Neon database provisioned
- [ ] Post-deploy smoke test
- [ ] Basic monitoring / error tracking

## Design system
- [ ] Decide whether to restyle `app/static/css/style.css` to the blue/green/white brand palette now documented in `README.md` — current CSS uses a different placeholder palette (cream/amber/brick) and this is a real visual overhaul, not a quick swap
- [ ] Swap in a transparent-background export of `logo.png` from the design source if you want to drop the CSS white-chip workaround currently used behind the footer logo

## Housekeeping
- [x] Add `app/static/logo.png` (referenced in the nav, footer, and favicon)
- [ ] Replace placeholder stats and testimonial on the landing page with real numbers before launch
- [ ] Add `LICENSE` file (README references MIT)
- [ ] Rotate any credentials that were ever pasted outside `.env`
