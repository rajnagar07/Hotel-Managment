"""Entry point for the Flask application with Supabase PostgreSQL.

This script creates the Flask app, initializes the database tables,
and starts the development server.
"""

from app import create_app, db
import sqlalchemy

app = create_app()


if __name__ == '__main__':
    """Initialize database and run the app."""
    # Create database tables if they don't exist. If the configured
    # DATABASE_URL is unreachable (e.g. Supabase host resolution failure),
    # fall back to a local SQLite file so local development can proceed.
    with app.app_context():
        try:
            db.create_all()
            print('[INFO] Database tables initialized successfully.')
        except Exception as e:
            # Log the original error
            print(f'[ERROR] Could not create tables: {e}')
            print('[HELP] Check your DATABASE_URL in .env and Supabase connection.')

            # If this looks like an operational/database connectivity error,
            # switch to a local SQLite DB and try again to allow local dev.
            err_text = str(e).lower()
            if isinstance(e, sqlalchemy.exc.OperationalError) or 'could not translate host name' in err_text or 'could not connect' in err_text:
                fallback_uri = 'sqlite:///hotel_dev.db'
                print(f'[INFO] Falling back to local SQLite database: {fallback_uri}')
                app.config['SQLALCHEMY_DATABASE_URI'] = fallback_uri
                try:
                    db.engine.dispose()
                    db.create_all()
                    print('[INFO] Database tables initialized successfully using SQLite fallback.')
                except Exception as e2:
                    print(f'[ERROR] SQLite fallback also failed: {e2}')
            else:
                print('[INFO] Error does not look like a connectivity issue. Not attempting fallback.')

    # Start the development server only when invoked directly.
    app.run(debug=app.config.get('DEBUG', False))
