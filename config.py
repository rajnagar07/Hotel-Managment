"""Flask configuration for Supabase PostgreSQL.

Load environment variables from .env file and provide defaults.
Use PostgreSQL URI format: postgresql://user:password@host:port/dbname
"""

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base configuration for the Flask application.

    Loads SECRET_KEY and DATABASE_URL from environment variables.
    Provides sensible defaults for local development.
    """
    # Secret key for session signing and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-in-production'

    # PostgreSQL database URI (supports Supabase)
    # Format: postgresql://user:password@host:port/database
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        # Fix for SQLAlchemy 1.4+ (convert postgres:// to postgresql://)
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'postgresql://localhost/hotel_db'

    # Disable modification tracking for performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pool configuration for better connection handling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,  # Test connections before using them
    }

    # File upload folders
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(basedir, 'uploads'))
    EXPORT_FOLDER = os.environ.get('EXPORT_FOLDER', os.path.join(basedir, 'exports'))
    HOTEL_UPLOAD_FOLDER = os.environ.get('HOTEL_UPLOAD_FOLDER', os.path.join(basedir, 'app', 'static', 'uploads', 'hotels'))

    # Mail configuration for admin password reset
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)


class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing-specific configuration."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
