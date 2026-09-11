# TODO — QuickFix Nearby

Tracking build-out of the marketplace described in `README.md`. Check items off as they land on `main`.

## Phase 1 — Foundation
- [ ] Flask app factory (`app/__init__.py`)
- [ ] Neon Postgres connection + SQLAlchemy setup
- [ ] Flask-Migrate / Alembic wired up
- [ ] `requirements.txt`
- [ ] `.env.example` (no real secrets, ever)
- [ ] `vercel.json` routing requests to the Flask WSGI app

## Phase 2 — Data models
- [ ] `users` — id, name, email, password_hash, role, google_id, profile_picture, created_at, updated_at
- [ ] `customers` — id, user_id, phone, location
- [ ] `professionals` — id, user_id, service_type, verified, rating, total_jobs, coverage_area
- [ ] `service_requests` — id, customer_id, professional_id, service_type, description, location, urgency, status, created_at
- [ ] `contact_submissions` — landing-page leads

## Phase 3 — Auth
- [ ] Email/password signup + login with hashed passwords
- [ ] Google OAuth flow
- [ ] Flask session management
- [ ] CSRF protection on every form (Flask-WTF)

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
- [x] Marketing landing page (`index.html`)
- [ ] Jinja2 templates for authenticated app views
- [ ] Move landing page into Tailwind build pipeline (currently hand-rolled CSS for the MVP)
- [ ] PWA manifest + service worker

## Phase 8 — AI/ML
- [ ] Hugging Face integration — e.g. auto-categorizing free-text job descriptions

## Phase 9 — Security & hardening
- [ ] Security headers: CSP, X-Frame-Options, X-Content-Type-Options
- [ ] Rate limiting on auth endpoints
- [ ] Input validation on every form and API route

## Phase 10 — Deployment
- [ ] Vercel project + env vars set (Production and Preview)
- [ ] Production Neon database provisioned
- [ ] Post-deploy smoke test
- [ ] Basic monitoring / error tracking

## Housekeeping
- [ ] Replace placeholder stats and testimonial on the landing page with real numbers before launch
- [ ] Add `LICENSE` file (README references MIT)
- [ ] Rotate any credentials that were ever pasted outside `.env`
