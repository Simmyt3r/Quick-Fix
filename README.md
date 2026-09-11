# QuickFix Nearby — Professional Service Marketplace

A marketplace platform connecting customers with verified, on-demand service professionals — electricians, plumbers, mechanics, builders, barbers, and more — across Nigeria.


## Overview

- **24/7 service booking** — customers request services anytime, specifying category, location, and urgency
- **Verified professionals** — pre-vetted providers with ratings, coverage areas, and identity verification
- **Live dashboard** — booking/service-request tracking for customers, professionals, and admins
- **Secure by default** — hashed credentials, CSRF protection, audit-friendly data model

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Hosting / deploy | Vercel (serverless functions 12 max) |
| Database | Neon (serverless Postgres) |
| Media storage | Cloudinary (profile photos, verification docs, job photos) |
| AI / ML | Hugging Face Inference API |
| Auth | Flask sessions + Google OAuth |
| Frontend | HTML5, TailwindCSS — PWA (manifest + service worker) |



## Core features

1. **Customer booking** — location-based requests, category selection, urgency level, scheduling
2. **Professional management** — profiles, availability, coverage area, ratings, earnings, verification
3. **Admin controls** — lead review, provider approval, incident tracking, reporting

### Service categories

⚡ Electrician · 🚰 Plumber · 🚗 Mechanic · 🧱 Builder · 💈 Barber · and more

## Data model (target)

Carried over conceptually from the current schema, moving to Postgres with a unified `users` table:

- **users** — id, name, email, password_hash, role (customer / professional / admin), google_id, profile_picture, created_at, updated_at
- **customers** — id, user_id, phone, location
- **professionals** — id, user_id, service_type, verified, rating, total_jobs, coverage_area
- **service_requests** — id, customer_id, professional_id (nullable), service_type, description, location, urgency, status, created_at
- **contact_submissions** — landing-page leads

## Proposed project structure

```
QuickFix/
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── models.py          # SQLAlchemy models
│   ├── routes/             # Blueprints: auth, booking, admin, api
│   ├── templates/          # Jinja2 templates
│   └── static/              # CSS/JS, manifest.webmanifest, sw.js
├── migrations/               # Flask-Migrate / Alembic
├── requirements.txt
├── vercel.json
├── .env.example
├── TODO.md
└── README.md
```

## Getting started

### Requirements

- Python 3.11+
- A [Neon](https://neon.tech) Postgres database
- A Cloudinary account (cloud name, API key/secret)
- A Hugging Face account + API token
- A Vercel account (for deployment)

### no Local setup


```

Create a `.env` file locally (never commit this — it should stay in `.gitignore`):

```env
FLASK_ENV=development
SECRET_KEY=change-me

# Neon Postgres
DATABASE_URL=postgresql://user:password@ep-xxxx.neon.tech/quickfix?sslmode=require

# Cloudinary
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# Hugging Face
HUGGINGFACE_API_TOKEN=

# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URL=http://localhost:5000/google-callback

MAIL_FROM=noreply@quickfix.ng
MAIL_ADMIN=admin@quickfix.ng
```

Run migrations and start the dev server:

```bash
flask db upgrade
flask run
```

Visit `http://localhost:5000`.

## Deployment (Vercel)

1. Push to GitHub and import the repo into Vercel.
2. Add the same environment variables from `.env` in the Vercel project settings (Production **and** Preview).
3. Add a `vercel.json` that routes requests to the Flask WSGI app.
4. Deploy — Vercel builds the Python serverless function automatically.

## Security

- No secrets in code — every credential above is read from an environment variable, with no hardcoded fallback value
- Passwords hashed, never stored in plain text
- CSRF protection on all forms (Flask-WTF)
- Security headers: CSP, X-Frame-Options, X-Content-Type-Options

## Support

- GitHub Issues: [Project Issues](https://github.com/Simmyt3r/QuickFix/issues)
- Email: support@quickfix.ng

## License

MIT License — see LICENSE file for details.

---

**Founder:** Nicazz Ishor
**Built with ❤️ for Nigeria 🇳🇬**
