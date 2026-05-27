# Hotel Management (Flask + Supabase PostgreSQL)

This is a beginner-friendly hotel management web application built with Flask, Bootstrap 5, **Supabase PostgreSQL**, SQLAlchemy, Pandas and OpenPyXL.

## Quick Start

1. **Get Supabase credentials:**
   - Sign up at [https://supabase.com](https://supabase.com)
   - Create a new project
   - Go to Project Settings > Database > Connection String (URI mode)
   - Copy the PostgreSQL connection string

2. **Configure environment:**
   ```bash
   # Copy .env.example to .env
   copy .env.example .env
   ```
   Edit `.env` and paste your Supabase connection string:
   ```
   DATABASE_URL=postgresql://postgres:your_password@db.xxxxx.supabase.co:5432/postgres
   SECRET_KEY=your-secure-key
   ```

3. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows PowerShell: . .\venv\Scripts\Activate.ps1
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the app:**
   ```bash
   python run.py
   ```
   The app will auto-create database tables on first run.
   Visit [http://localhost:5000](http://localhost:5000)

## Database Setup

- **Driver:** psycopg2-binary (PostgreSQL)
- **Database:** Supabase PostgreSQL
- **Automatic table creation:** Tables are created on app startup if they don't exist
- **Connection pooling:** Configured for optimal performance and reliability

## Features

- ✅ Supabase PostgreSQL backend
- ✅ User authentication with Flask-Login
- ✅ Admin dashboard
- ✅ Room management with image uploads
- ✅ Booking system
- ✅ Excel import/export (Pandas + OpenPyXL)
- ✅ Responsive Bootstrap 5 UI
- ✅ CSRF protection
- ✅ Password hashing

## Troubleshooting

**Connection Error:**
- Verify DATABASE_URL in `.env` is correct
- Check Supabase project is active
- Ensure your IP is allowed in Supabase firewall (usually auto-enabled)

**Module not found:**
- Make sure venv is activated: `. .\venv\Scripts\Activate.ps1` (PowerShell)
- Reinstall: `pip install -r requirements.txt`

**Table creation failed:**
- Verify PostgreSQL connection works first
- Check Supabase database exists
- Restart the app; tables auto-create on startup

## Project Structure

```
hotel-management/
├── app/
│   ├── static/      # CSS, JS, images
│   ├── templates/   # HTML templates
│   ├── routes/      # Flask blueprints
│   ├── models.py    # SQLAlchemy models
│   ├── forms.py     # WTForms
│   ├── services/    # Business logic (Excel utils)
│   └── __init__.py  # App factory
├── config.py        # Configuration (PostgreSQL)
├── run.py           # Entry point
├── requirements.txt # Python dependencies
├── .env.example     # Environment template (Supabase)
└── README.md        # This file
```

## Production Deployment

### Render.com (with Supabase)

1. Push code to GitHub
2. Connect GitHub to Render.com
3. Create Web Service
4. Set environment variables (DATABASE_URL from Supabase)
5. Deploy

### Manual VPS Deployment

```bash
# SSH to server
ssh user@your-vps

# Clone repository
git clone your-repo.git
cd hotel-management

# Create venv and install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://..."
export SECRET_KEY="..."

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## Database Models

- **User** - Admin/user accounts with password hashing
- **Room** - Hotel rooms with pricing and availability
- **Customer** - Guest information
- **Booking** - Room reservations with dates
- **Payment** - Payment records
- **Review** - Guest reviews and ratings

All models use proper PostgreSQL constraints, indexes, and relationships.

## Testing

```bash
# Activate venv and run
python run.py

# Access at http://localhost:5000
# Admin panel: http://localhost:5000/admin
```

## Support

- Check `.env.example` for configuration options
- Verify DATABASE_URL format is correct
- Ensure psycopg2-binary is installed: `pip install psycopg2-binary`
- Check Supabase status at [supabase.com/status](https://supabase.com/status)
