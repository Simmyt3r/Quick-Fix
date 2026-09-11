# QuickFix Nearby — Professional Service Marketplace

![QuickFix Nearby](app/static/logo.png)

A marketplace platform connecting customers with verified, on-demand service professionals — electricians, plumbers, mechanics, builders, barbers, and more — across Nigeria.

**Status:** early MVP. The landing page and lead capture are live; booking, auth, and the professional/admin dashboards are still ahead — see [`TODO.md`](TODO.md) for exactly what's built vs. planned.

## Overview

- **24/7 service booking** — customers request services anytime, specifying category, location, and urgency
- **Verified professionals** — pre-vetted providers with ratings, coverage areas, and identity verification
- **Live dashboard** — booking/service-request tracking for customers, professionals, and admins
- **Secure by default** — hashed credentials, CSRF protection, audit-friendly data model

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Hosting / deploy | Vercel (serverless functions) |
| Database | Neon (serverless Postgres) — not yet connected |
| Media storage | Cloudinary — not yet integrated |
| AI / ML | Hugging Face Inference API — not yet integrated |
| Auth | Flask sessions + Google OAuth — not yet built |
| Frontend | HTML5, hand-rolled CSS (Tailwind migration planned) |

## Core features (planned)

1. **Customer booking** — location-based requests, category selection, urgency level, scheduling
2. **Professional management** — profiles, availability, coverage area, ratings, earnings, verification
3. **Admin controls** — lead review, provider approval, incident tracking, reporting

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

> ⚠️ **Not yet applied.** The live landing page currently uses a different placeholder palette (cream background, amber CTAs, forest green, brick red — see `app/static/css/style.css`). Restyling to the palette above is tracked in `TODO.md`, pending confirmation.

**UX direction:** mobile-first, rounded cards, soft shadows, large touch targets, map-centric discovery ("Find & Fix It Fast"), verification badges, real professional photography. Primary flow: **Search → Find nearby pro → View profile → Book → Pay → Track → Rate.**

## Data model (target)

Not yet implemented (Phase 2) — planned as a unified `users` table plus role tables:

- **users** — id, name, email, password_hash, role (customer / professional / admin), google_id, profile_picture, created_at, updated_at
- **customers** — id, user_id, phone, location
- **professionals** — id, user_id, service_type, verified, rating, total_jobs, coverage_area
- **service_requests** — id, customer_id, professional_id (nullable), service_type, description, location, urgency, status, created_at
- **contact_submissions** — landing-page leads (currently just logged to stdout by `/leads`, not persisted)

## Project structure

```
Quick-Fix/
├── api/
│   └── index.py           # Vercel WSGI entrypoint
├── app/
│   ├── __init__.py         # Flask app factory
│   ├── routes/
│   │   └── main.py         # "/", "/healthz", "/leads"
│   ├── static/
│   │   ├── css/style.css
│   │   └── logo.png
│   └── templates/
│       └── index.html      # Marketing landing page
├── requirements.txt
├── vercel.json
├── .env.example
├── .gitignore
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
python run.py
```

Visit `http://localhost:5000`.

> `.env.example` already lists the Neon/Cloudinary/Hugging Face/Google variables ahead of time, but only `SECRET_KEY` and `FLASK_ENV` are actually read by the code today — the rest activate as each phase in `TODO.md` lands.

## Deployment (Vercel)

1. Push to GitHub and import the repo into Vercel.
2. Add the environment variables from `.env` in the Vercel project settings (Production **and** Preview) as each becomes needed.
3. `vercel.json` already routes all requests to `api/index.py` — confirm static assets under `app/static/` serve correctly on a real deploy (tracked in `TODO.md`).
4. Deploy — Vercel builds the Python serverless function automatically.

## Security

- No secrets in code — every credential is read from an environment variable, no hardcoded fallback values
- Passwords will be hashed, never stored in plain text (once auth lands)
- CSRF protection planned on all forms, including the public `/leads` form (Flask-WTF)
- Security headers (CSP, X-Frame-Options, X-Content-Type-Options) planned before launch

## Support

- GitHub Issues: [Project Issues](https://github.com/Simmyt3r/Quick-Fix/issues)
- Email: support@quickfix.ng

## License

MIT License — see `LICENSE` file for details. *(Not yet added — see `TODO.md`.)*

---

**Founder:** Nicazz Ishor
**Built with ❤️ for Nigeria 🇳🇬**
