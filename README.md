# QuickFix Nearby — Professional Service Marketplace

![QuickFix Nearby](app/static/logo.png)

A marketplace platform connecting customers with verified, on-demand service professionals — electricians, plumbers, mechanics, builders, barbers, and more — across Nigeria.

**Status:** early MVP. The landing page, lead capture, email/password + Google auth, a mobile-first PWA dashboard (tile grid, bottom nav, slide-out sidebar with Profile/Settings), and the core booking loop (customers request a service, matching professionals accept and complete it) are all live, backed by Postgres via SQLAlchemy + Flask-Migrate, with CSRF protection, rate limiting, security headers, and Cloudinary-backed profile photos in place. See [`TODO.md`](TODO.md) for exactly what's built vs. planned.

## Overview

- **24/7 service booking** — customers request services anytime, specifying category, description, location, and urgency; matching professionals accept and complete the job — live
- **Verified professionals** — providers get a verification badge (manual for now — no review queue yet) and only see requests in their own trade
- **Live dashboard** — full request lifecycle (pending → accepted → completed/cancelled) tracked for customers, professionals, and admins
- **Secure by default** — hashed credentials, CSRF-protected forms, rate-limited auth/lead endpoints, and a strict CSP

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Hosting / deploy | Vercel (serverless functions) |
| Database | Postgres (Neon-ready) via SQLAlchemy + Flask-Migrate — schema-managed, not yet pointed at a real Neon project |
| Media storage | Cloudinary — not yet integrated |
| AI / ML | Hugging Face Inference API — not yet integrated |
| Auth | Flask-Login — email/password (hashed) and Google OAuth (Authlib), both live |
| Frontend | HTML5, hand-rolled CSS (Tailwind migration planned) |

## Core features

1. **Customer booking** *(live)* — category selection, description, location, urgency; status tracking and self-service cancellation. Scheduling (a specific date/time, vs. just urgency) is still planned.
2. **Professional management** *(partial)* — accept/complete jobs in your own trade, verification badge display. Availability toggle, coverage area, ratings, and earnings are still planned.
3. **Admin controls** *(partial)* — dashboard with user/request/lead stats and recent activity tables. Provider approval queue, incident tracking, and deeper reporting are still planned.

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

**UX direction:** mobile-first, rounded cards, soft shadows, large touch targets, map-centric discovery ("Find & Fix It Fast"), verification badges, real professional photography. Primary flow: **Search → Find nearby pro → View profile → Book → Pay → Track → Rate.**

## Data model

Implemented so far (Phase 2 in progress) — a unified `users` table plus separate leads and service-request tables; a couple of role-specific tables are still planned:

- **users** *(live)* — id, name, email, password_hash (nullable for Google-only accounts), google_id, role (customer / professional / admin), service_category, verified, avatar_url, created_at, updated_at. `service_category`/`verified` are professional-only fields kept on this table for now rather than a separate `professionals` table.
- **contact_submissions** *(live)* — landing-page leads from `/leads`, shown on professional dashboards (filtered by category) and the admin dashboard (all leads)
- **service_requests** *(live)* — id, customer_id, professional_id (nullable until accepted), category, description, location, urgency, status (pending / accepted / completed / cancelled), created_at, updated_at. Both `customer_id` and `professional_id` are foreign keys to `users.id`.
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
│   ├── models.py             # User, ContactSubmission, ServiceRequest
│   ├── cli.py                # `flask create-admin`
│   ├── security.py           # response security headers (CSP, etc.)
│   ├── errors.py             # CSRF/rate-limit/payload-too-large error handlers
│   ├── uploads.py            # Cloudinary config + avatar upload helper
│   ├── routes/
│   │   ├── main.py           # "/", "/healthz", "/leads"
│   │   ├── auth.py           # "/register", "/login", "/logout", Google OAuth
│   │   ├── dashboard.py      # "/dashboard" (role-aware)
│   │   ├── requests.py       # "/requests/new", "/accept", "/complete", "/cancel"
│   │   └── profile.py        # "/profile", "/profile/update", "/profile/avatar", "/profile/settings"
│   ├── static/
│   │   ├── css/style.css
│   │   ├── js/                # sidebar.js, avatar-upload.js, register.js
│   │   ├── manifest.webmanifest, sw.js  # PWA
│   │   └── logo.png
│   └── templates/
│       ├── index.html        # Marketing landing page
│       ├── base_app.html     # Shared shell — sidebar, bottom nav, flash messages
│       ├── _sidebar.html     # Slide-out drawer (mobile) / persistent rail (desktop)
│       ├── auth/, dashboard/, requests/, profile/
├── migrations/                # Flask-Migrate/Alembic — `flask db upgrade`
├── .github/workflows/migrate.yml  # Manually-triggered `flask db upgrade` against production
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

> `.env.example` already lists the Cloudinary/Hugging Face/Google variables ahead of time, but only `SECRET_KEY`, `FLASK_ENV`, and `DATABASE_URL` are actually read by the code today — the rest activate as each phase in `TODO.md` lands.

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
- Rate limiting via Flask-Limiter — `/login` (10/min), `/register` (5/hr), `/leads` (10/hr) — live, but uses in-memory storage, so limits are per-process and won't hold across multiple serverless instances until a shared backend (e.g. Upstash Redis) is added
- Security headers on every response — CSP (no `unsafe-inline`), X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and HSTS over HTTPS — live

## Support

- GitHub Issues: [Project Issues](https://github.com/Simmyt3r/Quick-Fix/issues)
- Email: support@quickfix.ng

## License

MIT License — see `LICENSE` file for details. *(Not yet added — see `TODO.md`.)*

---

**Founder:** Nicazz Ishor
**Built with ❤️ for Nigeria 🇳🇬**
