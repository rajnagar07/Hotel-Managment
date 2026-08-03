
"""WTForms definitions used across the application.

Each form has clear field names and validators. Comments explain what
each form is for and which routes use them.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, BooleanField, TextAreaField, FileField, DateField, SelectField
from wtforms.validators import DataRequired, InputRequired, NumberRange, Length, Email, Optional, EqualTo, ValidationError
from flask_wtf.file import MultipleFileField, FileAllowed
from app.models import Admin


# -----------------------------
# Authentication forms
# -----------------------------
class LoginForm(FlaskForm):
    """Admin login form used by `admin.login` route."""
    identifier = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')


class AdminSignupForm(FlaskForm):
    """Admin signup form used by `admin.signup` route."""
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=120)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    role = SelectField('Account Type', choices=[('admin', 'Admin'), ('subadmin', 'Subadmin')], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Create Admin Account')

    def validate_username(self, username):
        if Admin.query.filter(Admin.username.ilike(username.data.strip())).first():
            raise ValidationError('Username already exists. Please choose another one.')

    def validate_email(self, email):
        if Admin.query.filter(Admin.email.ilike(email.data.strip())).first():
            raise ValidationError('Email already exists. Please use another email address.')


class ForgotPasswordForm(FlaskForm):
    """Request a password reset link for an admin account."""
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    """Set a new password using a verified reset token."""
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Reset Password')


class DeleteForm(FlaskForm):
    """Simple CSRF-protected delete confirmation form."""
    submit = SubmitField('Delete')


class HotelForm(FlaskForm):
    """Admin form for adding and editing hotel listings."""

    hotel_name = StringField('Hotel Name', validators=[DataRequired(), Length(min=2, max=150)])
    description = TextAreaField('Description', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(min=2, max=150)])
    # Use InputRequired so numeric zero (0) is accepted. Also enforce non-negative values.
    price = FloatField('Price per Night', validators=[InputRequired(), NumberRange(min=0)])
    room_type = StringField('Room Type', validators=[DataRequired(), Length(min=2, max=80)])
    amenities = TextAreaField('Amenities', validators=[DataRequired()], render_kw={'placeholder': 'Wi-Fi, Pool, Spa, Breakfast'})
    is_available = BooleanField('Available')
    room_id = SelectField('Linked Room (optional)', coerce=int, choices=[(-1, 'No linked room')])
    images = MultipleFileField(
        'Upload Images',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'jfif', 'png', 'webp'], 'Only JPG, JPEG, JFIF, PNG, and WEBP images are allowed.'),
        ],
        render_kw={'accept': '.jpg,.jpeg,.jfif,.png,.webp,image/jpeg,image/png,image/webp', 'multiple': True},
    )
    submit = SubmitField('Save Hotel')


# -----------------------------
# Room management form
# -----------------------------
class RoomForm(FlaskForm):
    """Form to create or edit a Room record in the admin panel."""
    number = StringField('Room Number', validators=[DataRequired(), Length(max=20)])
    room_type = StringField('Room Type', validators=[DataRequired()])
    # Use InputRequired to allow 0 as a valid price and ensure non-negative values.
    price = FloatField('Price', validators=[InputRequired(), NumberRange(min=0)])
    ac = BooleanField('AC')
    availability = BooleanField('Available')
    description = TextAreaField('Description', validators=[Optional()])
    images = FileField(
        'Images',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'jfif', 'png', 'webp'], 'Only JPG, JPEG, JFIF, PNG, and WEBP images are allowed.'),
        ],
        render_kw={'accept': '.jpg,.jpeg,.jfif,.png,.webp,image/jpeg,image/png,image/webp'},
    )
    submit = SubmitField('Save')


# -----------------------------
# Booking form (user-facing)
# -----------------------------
class BookingForm(FlaskForm):
    """Customer booking form used on room pages to collect guest details and dates."""
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    check_in = DateField('Check-in', validators=[DataRequired()])
    check_out = DateField('Check-out', validators=[DataRequired()])
    submit = SubmitField('Book Now')


# -----------------------------
# Excel upload form
# -----------------------------
class ExcelUploadForm(FlaskForm):
    """Used to upload Excel files for preview and processing in admin flows."""
    file = FileField('Excel File', validators=[DataRequired()])
    submit = SubmitField('Upload')

