# QuickFix Nearby — Professional Service Marketplace

![QuickFix Nearby](app/static/logo.png)

A marketplace platform connecting customers with verified, on-demand service professionals — electricians, plumbers, mechanics, builders, barbers, and more — across Nigeria.

**Status:** early MVP. The landing page, lead capture, email/password + Google auth (with a full password reset flow via email), a mobile-first PWA dashboard (tile grid, bottom nav, slide-out sidebar with Profile/Settings), the core booking loop (customers request a service, matching professionals accept and complete it, then rate it 1–5 stars), and a full admin suite (professional verification queue, user management with disable/enable, incident logging, and an audit log) are all live, backed by Postgres via SQLAlchemy + Flask-Migrate, with CSRF protection, rate limiting, security headers, and Cloudinary-backed profile photos in place. Accounts can be customer, professional, or both at once. **End-to-end smoke-tested on the live production site (quickfixnearby.vercel.app) on 2026-09-16 — registration (including a dual-role account), login, and dashboard all confirmed working against the real Neon database.** See [`TODO.md`](TODO.md) for exactly what's built vs. planned.

## Overview

- **24/7 service booking** — customers request services anytime, specifying category, description, location, and urgency; matching professionals accept and complete the job — live
- **Verified professionals** — providers get a verification badge, reviewed and approved by an admin through a dedicated queue (`/admin/verification`); unverified professionals are blocked from accepting jobs
- **Ratings & reviews** — once a job is marked complete, the customer can rate it 1–5 stars with an optional comment; the professional's average rating shows on their own dashboard, and publicly on the professional directory and their profile page. One review per job.
- **Public professional directory** — `/pros/` (browsable, filterable by category) and `/pros/<id>` (profile with average rating and recent reviews), unauthenticated. A customer can request a specific professional directly from their profile ("Request this pro"), which locks the booking to that pro's trade and only they can accept it.
- **Live dashboard** — full request lifecycle (pending → accepted → completed/cancelled) tracked for customers, professionals, and admins
- **Account recovery** — self-service password reset via a time-limited emailed link (Gmail SMTP); Google-only accounts get a clear "sign in with Google instead" email rather than a broken reset link
- **Secure by default** — hashed credentials, CSRF-protected forms, rate-limited auth/lead endpoints, and a strict CSP

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Hosting / deploy | Vercel (serverless functions) |
| Database | Postgres (Neon) via SQLAlchemy + Flask-Migrate — live at quickfixnearby.vercel.app, migrations applied via a manually-triggered GitHub Actions workflow |
| Media storage | Cloudinary — live, powers profile photo uploads |
| AI / ML | Hugging Face Inference API — not yet integrated |
| Auth | Flask-Login — email/password (hashed) and Google OAuth (Authlib), both live |
| Frontend | HTML5, hand-rolled CSS (Tailwind migration planned) |

## Core features

1. **Customer booking** *(live)* — category selection, description, location, urgency; status tracking, self-service cancellation, and a 1–5 star rating with optional comment once a job is complete. Scheduling (a specific date/time, vs. just urgency) is still planned.
2. **Professional management** *(partial)* — accept/complete jobs in your own trade, verification badge display, average rating shown on your own dashboard and on your public profile. A customer can book you directly from that profile. Availability toggle, coverage area, and earnings are still planned.
3. **Admin controls** *(live)* — dashboard with user/request/lead stats and recent activity tables; a verification queue to approve/reject professionals; user management with search, filtering, and account disable/enable; incident logging (no-shows, disputes, complaints) tied to a user and/or service request; and a full audit log of every admin action. Deeper reporting (trends, exports) beyond the current counts/tables is still planned.

### Service categories

⚡ Electrician · 🚰 Plumber · 🚗 Mechanic · 🧱 Builder · 💈 Barber · and more

## Design & branding

**Logo:** a blue map pin combined with a wrench, with a green checkerboard accent — reads as *location + repair + speed*.

**Target color palette:**

| Color | Hex | Role |
|---|---|---|
| Primary Blue | `#0068B7` | Headers, navigation, buttons |
| Bright Blue | `#168BE0` | Branding, highlights, map elements |
| Primary Green | `#20A84A` | Booking, success, verification |
| Dark Green | `#168447` | Logo/text accents |
| White | `#FFFFFF` | Backgrounds, cards |
| Light Gray | `#F2F4F5` | Card/section backgrounds |
| Yellow/Gold | `#F5B51B` | Ratings, stars |
| Orange/Red | — | Map pins, urgency indicators |
| Dark Gray | `#263238` | Body text |

✅ **Applied.** `app/static/css/style.css` uses this palette (`--blue`, `--green`, `--gold`, etc.) — screenshot-tested at desktop and mobile widths.

**UX direction:** mobile-first, rounded cards, soft shadows, large touch targets, map-centric discovery ("Find & Fix It Fast"), verification badges, real professional photography. Primary flow: **Search → Find nearby pro → View profile → Book → Pay → Track → Rate.** Find, View profile, Book, Track, and Rate are all live via the public directory (`/pros/`) and "Request this pro." Search (free-text, vs. just a category filter) and Pay (in-app payment) are still planned.

## Data model

Implemented so far (Phase 2 in progress) — a unified `users` table plus separate leads and service-request tables; a couple of role-specific tables are still planned:

- **users** *(live)* — id, name, email, password_hash (nullable for Google-only accounts), google_id, is_customer, is_professional (independent flags — an account can be either or both), role (admin-only flag; not used for customer/professional anymore), service_category, verified, disabled, reset_token, reset_token_expires, avatar_url, created_at, updated_at. `service_category`/`verified` are professional-only fields kept on this table for now rather than a separate `professionals` table. `disabled` is admin-managed account status — a disabled user is blocked at login and any active session is killed on their next request. `reset_token`/`reset_token_expires` back the password-reset flow — a random single-use string, not a signed token, cleared the moment it's redeemed.
- **contact_submissions** *(live)* — landing-page leads from `/leads`, shown on professional dashboards (filtered by category) and the admin dashboard (all leads)
- **service_requests** *(live)* — id, customer_id, professional_id (nullable until accepted), requested_professional_id (nullable — set when booked via "Request this pro"; if set, only that professional can accept), category, description, location, urgency, status (pending / accepted / completed / cancelled), created_at, updated_at. `customer_id`, `professional_id`, and `requested_professional_id` are all foreign keys to `users.id`.
- **reviews** *(live)* — id, service_request_id (unique — one review per job), customer_id, professional_id, rating (1–5), comment (optional), created_at. Customer-to-professional only for now; a reverse direction would need a `direction` column rather than a new table.
- **incidents** *(live)* — id, reported_by_id, subject_user_id, service_request_id, category (no_show / dispute / complaint / other), note, status (open / resolved), created_at, resolved_at. An admin-logged report attachable to a user and/or a service request.
- **admin_actions** *(live)* — id, admin_id, action, target_user_id, target_incident_id, detail, created_at. Audit trail — every admin action (verify, reject, disable, enable, log incident, resolve incident) is recorded automatically.
- **customers** *(planned)* — id, user_id, phone, location
- **professionals** *(planned)* — id, user_id, service_type, verified, rating, total_jobs, coverage_area — will absorb `service_category`/`verified` off of `users`

Schema is managed by Flask-Migrate (Alembic) — see `migrations/`. Run `flask db upgrade` to apply.

## Project structure

```
Quick-Fix/
├── api/
│   └── index.py             # Vercel WSGI entrypoint
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── extensions.py         # db, login_manager, migrate, csrf, limiter, oauth
│   ├── models.py             # User, ContactSubmission, ServiceRequest, Review, Incident, AdminAction
│   ├── cli.py                # `flask create-admin`
│   ├── security.py           # response security headers (CSP, etc.)
│   ├── errors.py             # CSRF/rate-limit/payload-too-large error handlers
│   ├── uploads.py            # Cloudinary config + avatar upload helper
│   ├── mail.py                # Gmail SMTP sender for password-reset emails, degrades gracefully if unconfigured
│   ├── routes/
│   │   ├── main.py           # "/", "/healthz", "/leads"
│   │   ├── auth.py           # "/register", "/login", "/logout", "/forgot-password", "/reset-password/<token>", Google OAuth
│   │   ├── dashboard.py      # "/dashboard" (role-aware)
│   │   ├── requests.py       # "/requests/new", "/accept", "/complete", "/cancel", "/review"
│   │   ├── profile.py        # "/profile", "/profile/update", "/profile/avatar", "/profile/settings"
│   │   ├── admin.py          # "/admin/verification", "/admin/users", "/admin/incidents", "/admin/activity"
│   │   └── pros.py           # "/pros/" (public directory), "/pros/<id>" (public profile)
│   ├── static/
│   │   ├── css/style.css
│   │   ├── css/splash.css     # standalone landing-page styles (index.html doesn't use style.css)
│   │   ├── js/                # sidebar.js, avatar-upload.js, register.js, profile-role.js, service-worker-register.js, admin-reject-toggle.js, admin-disable-toggle.js, review-toggle.js
│   │   ├── manifest.webmanifest, sw.js  # PWA
│   │   └── logo.png
│   └── templates/
│       ├── index.html        # Marketing landing page
│       ├── base_app.html     # Shared shell — sidebar, bottom nav, flash messages
│       ├── _sidebar.html     # Slide-out drawer (mobile) / persistent rail (desktop) — Admin section visible only to admins
│       ├── pros/              # directory.html, profile.html — public, no login required
│       ├── auth/              # login, register, forgot_password, reset_password
│       ├── dashboard/, requests/, profile/, admin/
├── migrations/                # Flask-Migrate/Alembic — `flask db upgrade`
├── .github/workflows/migrate.yml       # Manually-triggered `flask db upgrade` against production
├── .github/workflows/create-admin.yml  # Manually-triggered `flask create-admin` (creates or promotes) against production
├── requirements.txt
├── vercel.json
├── .env.example
├── .gitignore
├── run.py
├── README.md
└── TODO.md
```

## Getting started

### Requirements

- Python 3.11+
- (Later phases) a [Neon](https://neon.tech) Postgres database, a Cloudinary account, a Hugging Face API token, a Google OAuth client — see `.env.example`

### Local setup

```bash
git clone https://github.com/Simmyt3r/Quick-Fix.git
cd Quick-Fix
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
flask db upgrade   # creates the schema — SQLite by default, or Postgres if DATABASE_URL is set
python run.py
```

Visit `http://localhost:5000`. To try the admin dashboard, create an admin from the CLI:

```bash
flask create-admin you@example.com yourpassword
```

> `.env.example` already lists the Cloudinary/Hugging Face/Google variables ahead of time, but only `SECRET_KEY`, `FLASK_ENV`, `DATABASE_URL`, `GOOGLE_CLIENT_ID`/`SECRET`, `CLOUDINARY_URL`, and `SMTP_USERNAME`/`SMTP_PASSWORD` are actually read by the code today — the rest activate as each phase in `TODO.md` lands. Without SMTP configured, password-reset links are logged to the server console instead of emailed, so the flow stays testable locally with no real credentials.

## Deployment (Vercel)

1. Provision a [Neon](https://neon.tech) project and copy its connection string into `DATABASE_URL`.
2. Push to GitHub and import the repo into Vercel.
3. Add the environment variables from `.env` in the Vercel project settings (Production **and** Preview) as each becomes needed.
4. Run `flask db upgrade` against the production `DATABASE_URL` once, from a machine that can reach it — Vercel's serverless functions shouldn't run migrations on every cold start.
5. `vercel.json` already routes all requests to `api/index.py` — confirm static assets under `app/static/` serve correctly on a real deploy (tracked in `TODO.md`).
6. Deploy — Vercel builds the Python serverless function automatically.

## Security

- No secrets in code — every credential is read from an environment variable, no hardcoded fallback values
- Passwords are hashed with Werkzeug, never stored in plain text — live
- CSRF protection on every form (`/leads`, `/login`, `/register`) via Flask-WTF — live
- Rate limiting via Flask-Limiter — `/login` (10/min), `/register` (5/hr), `/forgot-password` (5/hr), `/reset-password/<token>` (10/hr), `/leads` (10/hr) — live, but uses in-memory storage, so limits are per-process and won't hold across multiple serverless instances until a shared backend (e.g. Upstash Redis) is added
- Security headers on every response — CSP (no `unsafe-inline`), X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and HSTS over HTTPS — live

## Support

- GitHub Issues: [Project Issues](https://github.com/Simmyt3r/Quick-Fix/issues)
- Email: support@quickfix.ng

## License

MIT License — see [`LICENSE`](LICENSE) for details.

---

**Founder:** Nicazz Ishor
**Built with ❤️ for Nigeria 🇳🇬**
