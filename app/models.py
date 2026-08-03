"""Database models for hotel booking app with Supabase PostgreSQL.

This module defines SQLAlchemy models for Supabase PostgreSQL backend.
All models use proper relationships, cascading deletes, and constraints
optimized for PostgreSQL. The Flask-Login user loader is also defined.
Comments explain each model and important fields so beginners can follow.

Database: Supabase PostgreSQL (psycopg2-binary driver)
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


# -----------------------------
# Flask-Login user loader
# -----------------------------
@login_manager.user_loader
def load_user(user_id):
    """Given a user_id, return the corresponding Admin object.

    - Used by Flask-Login to reload the user from the session.
    """
    return Admin.query.get(int(user_id))


# -----------------------------
# Admin model
# -----------------------------
class Admin(UserMixin, db.Model):
    """Admin account table.

    Fields:
    - full_name: admin display name
    - username: login name
    - email: contact email
    - password_hash: hashed password (never store plain text)
    - created_at: registration timestamp
    - is_admin: flag for admin privileges
    - role: distinguishes full admins from subadmins
    - is_verified: subadmin approval flag
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=True, nullable=False)
    role = db.Column(db.String(20), default='admin', nullable=False)
    is_verified = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, password):
        """Hash and store the admin password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_subadmin(self):
        return (self.role or 'admin') == 'subadmin'


# -----------------------------
# Room model
# -----------------------------
class Room(db.Model):
    """Rooms available for booking.

    - `images` stores comma-separated filenames for simplicity.
    - `bookings` relationship links to Booking records.
    """
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    ac = db.Column(db.Boolean, default=True)
    availability = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
    images = db.Column(db.Text)  # comma separated filenames

    bookings = db.relationship('Booking', backref='room', lazy=True)


# -----------------------------
# Hotel model
# -----------------------------
class Hotel(db.Model):
    """Hotel listing table used for the public hotel catalog.

    Each hotel has a one-to-many relationship with HotelImage.
    """

    id = db.Column(db.Integer, primary_key=True)
    hotel_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    room_type = db.Column(db.String(80), nullable=False)
    amenities = db.Column(db.Text, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship('HotelImage', backref='hotel', cascade='all, delete-orphan', lazy=True, order_by='HotelImage.created_at.asc()')

    @property
    def cover_image_url(self):
        """Return the first hotel image URL if available."""
        return self.images[0].image_url if self.images else None

    @property
    def amenities_list(self):
        """Return amenities as a cleaned list for template rendering."""
        return [item.strip() for item in (self.amenities or '').split(',') if item.strip()]


# -----------------------------
# Hotel image model
# -----------------------------
class HotelImage(db.Model):
    """Stores uploaded image paths for a hotel."""

    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -----------------------------
# Customer model
# -----------------------------
class Customer(db.Model):
    """Customer contact and profile information."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    bookings = db.relationship('Booking', backref='customer', lazy=True)


# -----------------------------
# Booking model
# -----------------------------
class Booking(db.Model):
    """Booking record linking a customer to a room and dates."""
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    check_in = db.Column(db.Date)
    check_out = db.Column(db.Date)
    total_price = db.Column(db.Float)
    status = db.Column(db.String(50), default='confirmed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -----------------------------
# Payment model
# -----------------------------
class Payment(db.Model):
    """Simple payment record associated to a booking."""
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'))
    amount = db.Column(db.Float)
    method = db.Column(db.String(50))
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)

