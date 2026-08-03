"""Setup script for Hotel Management Flask + Supabase PostgreSQL.

This script helps with initial setup:
- Creating database tables
- Creating a default admin user
- Verifying Supabase connection

Usage:
    python setup.py

Prerequisites:
- Virtual environment activated
- Dependencies installed: pip install -r requirements.txt
- .env file with DATABASE_URL configured
"""

import os
import sys
from sqlalchemy import text
from app import create_app, db
from app.models import Admin


def _required_env(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise RuntimeError(f'Missing required environment variable for setup.py: {name}')
    return value


def setup_database():
    """Create all database tables."""
    print('\n[1] Creating database tables...')
    try:
        with app.app_context():
            db.create_all()
            print('✓ Database tables created successfully!\n')
            return True
    except Exception as e:
        print(f'✗ Error creating tables: {e}\n')
        print('TROUBLESHOOTING:')
        print('  - Check DATABASE_URL in .env is correct')
        print('  - Verify Supabase project is active')
        print('  - Ensure your IP is allowed in Supabase firewall')
        return False
def create_admin_user():
    """Create or refresh the default admin user."""
    print('[2] Creating admin user...')
    try:
        with app.app_context():
            # Make sure the admin columns exist for the updated model
            db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS full_name VARCHAR(120) NOT NULL DEFAULT ''"))
            db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS created_at TIMESTAMP NOT NULL DEFAULT NOW()"))
            db.session.execute(text("ALTER TABLE \"user\" ALTER COLUMN is_admin SET DEFAULT TRUE"))
            db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'admin'"))
            db.session.execute(text("ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT TRUE"))

            default_username = _required_env('DEFAULT_ADMIN_USERNAME')
            default_email = _required_env('DEFAULT_ADMIN_EMAIL')
            default_password = _required_env('DEFAULT_ADMIN_PASSWORD')
            default_full_name = os.environ.get('DEFAULT_ADMIN_FULL_NAME', 'Hotel Administrator').strip() or 'Hotel Administrator'

            admin = Admin.query.filter_by(username=default_username).first()
            if not admin:
                admin = Admin(
                    full_name=default_full_name,
                    username=default_username,
                    email=default_email,
                    is_admin=True,
                )
                admin.set_password(default_password)
                db.session.add(admin)
            else:
                admin.full_name = admin.full_name or default_full_name
                admin.email = default_email
                admin.is_admin = True
                admin.set_password(default_password)

            db.session.commit()
            print('✓ Admin user created successfully!')
            print(f'  Username: {default_username}')
            print(f'  Email: {default_email}')
            print('  Password: provided via DEFAULT_ADMIN_PASSWORD\n')
            return True
    except Exception as e:
        print(f'✗ Error creating admin: {e}\n')
        return False


def verify_connection():
    """Verify PostgreSQL connection works."""
    print('[3] Verifying Supabase connection...')
    try:
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            print('✓ PostgreSQL connection successful!\n')
            return True
    except Exception as e:
        print(f'✗ Connection failed: {e}\n')
        print('TROUBLESHOOTING:')
        print('  - Ensure DATABASE_URL is set in .env')
        print('  - Format: postgresql://user:password@host:port/database')
        print('  - Test connection: psql postgresql://...')
        return False


if __name__ == '__main__':
    app = create_app()

    print('\n' + '='*60)
    print('Hotel Management - Supabase PostgreSQL Setup')
    print('='*60)

    # Check if .env exists
    if not os.path.exists('.env'):
        print('\n✗ .env file not found!')
        print('Please copy .env.example to .env and fill in your Supabase credentials.')
        sys.exit(1)

    # Check DATABASE_URL
    if not os.getenv('DATABASE_URL'):
        print('\n✗ DATABASE_URL not set in .env!')
        print('Add: DATABASE_URL=postgresql://...')
        sys.exit(1)

    # Run setup steps
    success = True
    success &= verify_connection()
    success &= setup_database()
    success &= create_admin_user()

    if success:
        print('='*60)
        print('✓ Setup completed successfully!')
        print('='*60)
        print('\nNext steps:')
        print('  1. Run: python run.py')
        print('  2. Visit: http://localhost:5000')
        print('  3. Admin panel: http://localhost:5000/admin')
        print('  4. Login with username: admin')
        print('\n')
    else:
        print('='*60)
        print('✗ Setup encountered errors. See above for details.')
        print('='*60 + '\n')
        sys.exit(1)
