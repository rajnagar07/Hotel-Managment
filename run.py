"""Entry point for the Flask application with Supabase PostgreSQL.

This script creates the Flask app, initializes the database tables,
and starts the development server.
"""

from app import create_app, db

app = create_app()


if __name__ == '__main__':
    """Initialize database and run the app."""
    # Schema changes belong in setup.py/migrations, never in a production
    # web worker. Auto-creation remains available for local development.
    if app.config.get('AUTO_CREATE_DB'):
        with app.app_context():
            db.create_all()
            print('[INFO] Database tables initialized successfully.')

    # Start the development server only when invoked directly.
    app.run(debug=app.config.get('DEBUG', False))
