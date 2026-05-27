"""Application factory for the hotel booking app with Supabase PostgreSQL.

This module initializes Flask, SQLAlchemy, and Flask-Login.
It also registers blueprints and ensures upload/export folders exist.
Comments describe each startup step for beginners.

Database: Uses Supabase PostgreSQL via psycopg2-binary driver.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

# Initialize extensions (they will be bound to app in create_app)
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
login_manager.login_view = 'admin.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    """Create and configure the Flask application instance.

    Steps:
    1. Create Flask app and load configuration from `config_class`.
    2. Initialize extensions (db, login_manager) with PostgreSQL settings.
    3. Ensure filesystem folders exist for uploads and exports.
    4. Register blueprints for main and admin routes.
    5. Set up error handlers for database issues.
    """
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config_class)

    # Bind extensions to app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Ensure upload/export folders exist so file operations won't fail
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    os.makedirs(app.config.get('EXPORT_FOLDER', 'exports'), exist_ok=True)
    os.makedirs(app.config.get('HOTEL_UPLOAD_FOLDER', os.path.join(app.static_folder, 'uploads', 'hotels')), exist_ok=True)

    # Import blueprints late to avoid circular imports
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.context_processor
    def inject_globals():
        """Expose shared template values like the current year."""
        from datetime import datetime
        return {'current_year': datetime.utcnow().year}

    return app
