# Hotel Management (Flask + Supabase PostgreSQL)

Production-oriented hotel management app built with Flask, SQLAlchemy, WTForms, and Supabase PostgreSQL.

## What this app includes

- Public hotel and room listing pages
- Booking flow for customers
- Admin dashboard for hotel/room content management
- Public **subadmin signup** with **admin verification** workflow
- Excel-based import and enquiry export utilities
- CSRF protection and password hashing

## Tech stack

- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-WTF
- Supabase PostgreSQL (`psycopg2-binary`)
- Gunicorn (WSGI)
- Nginx (reverse proxy/static)

## Local setup (Windows PowerShell)

1. Clone and enter the project.
2. Create and activate venv.
3. Install dependencies.
4. Create `.env` from `.env.example`.
5. Run one-time setup.
6. Start the app.

```powershell
python -m venv venv
. .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python setup.py
python run.py
```

Open:

- Home: `http://127.0.0.1:5000`
- Admin login: `http://127.0.0.1:5000/admin/login`

## Admin and subadmin account flow

- If no admin exists, `/admin/signup` can create the **first admin**.
- After that, public signup is limited to **subadmin** creation.
- Subadmins cannot access dashboard until verified by an admin.
- Admin verifies pending subadmins from the dashboard section:
  - **Subadmin Verification**

## Environment variables

Use `.env.example` as the source of truth. Minimum required for runtime:

- `SECRET_KEY`
- `DATABASE_URL`

Strongly recommended for production:

- `FLASK_ENV=production`
- `FLASK_DEBUG=0`
- `SESSION_COOKIE_SECURE=1`
- `SESSION_COOKIE_HTTPONLY=1`
- `MAX_CONTENT_LENGTH=16777216`

Setup/bootstrap variables used by `setup.py`:

- `DEFAULT_ADMIN_USERNAME`
- `DEFAULT_ADMIN_EMAIL`
- `DEFAULT_ADMIN_PASSWORD`
- `DEFAULT_ADMIN_FULL_NAME` (optional)

## Database initialization and migrations

Run this after first clone and after model changes:

```bash
python setup.py
```

`setup.py` handles:

- table creation
- required column backfills
- admin bootstrap/update

## Production deployment (VPS)

Use the included templates:

- `gunicorn.conf.py`
- `hotel-management.service`
- `nginx.conf.example`

Recommended order:

1. Clone repo on VPS
2. Create venv and install requirements
3. Create `.env` with production values
4. Run `python setup.py`
5. Install and start `hotel-management.service`
6. Configure Nginx from `nginx.conf.example`
7. Set up SSL with Certbot

## Useful files

- `config.py` — app configuration
- `run.py` — Flask app entry point
- `setup.py` — one-time setup and schema backfills
- `app/models.py` — SQLAlchemy models
- `app/routes/admin.py` — admin auth, verification, and dashboard
- `DEPLOYMENT.md` — detailed deployment guide
- `MIGRATION.md` — migration notes

## Troubleshooting

### Login works but signup won’t create admin

Expected if an admin already exists and user is not logged in.
Public signup creates subadmins only (who need admin verification).

### `column user.role does not exist`

Run:

```bash
python setup.py
```

### App fails at startup

Check:

- `.env` exists
- `SECRET_KEY` is set
- `DATABASE_URL` is valid and reachable

## Security notes

- Never commit `.env`
- Rotate credentials immediately if secrets were exposed
- Keep uploaded media folders backed up on VPS
- Prefer HTTPS-only access in production
