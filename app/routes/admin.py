"""Admin routes for the application with Supabase PostgreSQL backend.

This module defines routes used by site administrators for logging in,
managing rooms and hotels, and handling Excel uploads to PostgreSQL.
"""

from flask import abort, render_template, request, redirect, url_for, flash, current_app, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.utils import secure_filename
import os
import uuid
from app.routes import admin_bp
from functools import wraps
from sqlalchemy import func, or_
from sqlalchemy.exc import OperationalError
from app import db, mail
from app.models import Admin, Room, Booking, Hotel, HotelImage
from app.forms import LoginForm, AdminSignupForm, ForgotPasswordForm, ResetPasswordForm, RoomForm, ExcelUploadForm, HotelForm, DeleteForm
from app.services.hotel_utils import save_hotel_images, delete_hotel_image_file
from app.services.excel_utils import read_excel_preview, process_excel_upload


def admin_required(view):
    """Ensure only authenticated admins can reach a view."""

    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not getattr(current_user, 'is_admin', False):
            flash('Admin access required.', 'danger')
            return redirect(url_for('admin.login'))
        if getattr(current_user, 'role', 'admin') == 'subadmin' and not getattr(current_user, 'is_verified', False):
            flash('Your subadmin account is pending verification.', 'warning')
            return redirect(url_for('admin.login'))
        return view(*args, **kwargs)

    return wrapped


def admin_only(view):
    """Restrict sensitive account and destructive actions to full admins."""
    @wraps(view)
    @admin_required
    def wrapped(*args, **kwargs):
        if getattr(current_user, 'role', 'admin') == 'subadmin':
            flash('This action is available to full admins only.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return view(*args, **kwargs)
    return wrapped


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='admin-password-reset')


def generate_reset_token(admin):
    return _serializer().dumps(admin.email)


def verify_reset_token(token, max_age=3600):
    try:
        email = _serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    return Admin.query.filter(func.lower(Admin.email) == email.lower(), Admin.is_admin.is_(True)).first()


def send_reset_email(admin, token):
    reset_url = url_for('admin.reset_password', token=token, _external=True)
    msg = Message('Reset your Family Hotel admin password', recipients=[admin.email])
    msg.body = (
        f"Hello {admin.full_name or admin.username},\n\n"
        f"A password reset was requested for your admin account.\n"
        f"Use the link below to reset your password:\n\n"
        f"{reset_url}\n\n"
        f"This link expires in 1 hour. If you did not request a reset, you can safely ignore this email."
    )
    msg.html = f"""
    <p>Hello {admin.full_name or admin.username},</p>
    <p>A password reset was requested for your admin account.</p>
    <p><a href="{reset_url}">Reset your password</a></p>
    <p>This link expires in 1 hour. If you did not request a reset, you can safely ignore this email.</p>
    """
    mail.send(msg)


def _mail_is_configured():
    """Return True when the app has enough SMTP configuration to send mail."""
    cfg = current_app.config
    username = (cfg.get('MAIL_USERNAME') or '').strip()
    password = (cfg.get('MAIL_PASSWORD') or '').strip()
    sender = (cfg.get('MAIL_DEFAULT_SENDER') or '').strip()

    placeholder_values = {
        'your_email@example.com',
        'your_email_app_password',
        'change-me',
        'changeme',
        'placeholder',
    }

    return all([
        cfg.get('MAIL_SERVER'),
        username,
        password,
        sender,
        username.lower() not in placeholder_values,
        password.lower() not in placeholder_values,
        sender.lower() not in placeholder_values,
    ])


def _serialize_hotel(hotel):
    """Convert a hotel ORM object into a JSON-friendly dictionary."""
    return {
        'id': hotel.id,
        'hotel_name': hotel.hotel_name,
        'description': hotel.description,
        'location': hotel.location,
        'price': hotel.price,
        'room_type': hotel.room_type,
        'amenities': hotel.amenities_list,
        'is_available': hotel.is_available,
        'room_id': hotel.room_id,
        'cover_image_url': hotel.cover_image_url,
        'images': [{'id': image.id, 'image_url': image.image_url} for image in hotel.images],
        'created_at': hotel.created_at.isoformat() if hotel.created_at else None,
    }


def _room_choices():
    """Build SelectField choices for rooms so hotels can link to a room."""
    choices = [(-1, 'No linked room')]
    choices.extend([(room.id, f'{room.number} — {room.room_type}') for room in Room.query.order_by(Room.number.asc()).all()])
    return choices


def _room_image_url(image):
    """Return the stored room image filename without allowing path traversal."""
    if not image:
        return None
    return os.path.basename(str(image).replace('\\', '/'))


def _delete_room_image_file(filename):
    """Delete a room image from the configured upload directory."""
    safe_name = _room_image_url(filename)
    if not safe_name:
        return
    image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_name)
    if os.path.isfile(image_path):
        os.remove(image_path)


# -----------------------------
# Admin login/logout routes
# -----------------------------
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle admin login.

    - Accepts username or email.
    - Redirects authenticated admins to the dashboard.
    """
    if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
        return redirect(url_for('admin.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = (form.identifier.data or '').strip().lower()
        try:
            admin = Admin.query.filter(
                or_(func.lower(Admin.username) == identifier, func.lower(Admin.email) == identifier)
            ).first()
        except OperationalError:
            # Supabase can briefly reject connections during maintenance or
            # failover. Show a usable response instead of Flask's debugger.
            db.session.rollback()
            current_app.logger.exception('Database unavailable during admin login')
            flash('The database is temporarily unavailable. Please try again shortly.', 'danger')
            return render_template('admin/login.html', form=form), 503
        if admin and admin.check_password(form.password.data):
            if getattr(admin, 'role', 'admin') == 'subadmin' and not getattr(admin, 'is_verified', False):
                flash('Your subadmin account is awaiting verification.', 'warning')
                return render_template('admin/login.html', form=form)
            login_user(admin, remember=form.remember_me.data)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('admin/login.html', form=form)


@admin_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Create the first admin or allow logged-in admins to add more admins.

    - If no admin accounts exist yet, the page is public so the first
      administrator can be created.
    - If admins already exist, only a logged-in admin may create another one.
    """
    admin_count = Admin.query.count()
    is_admin_user = current_user.is_authenticated and getattr(current_user, 'is_admin', False)
    is_verified_admin = (
        is_admin_user
        and (
            getattr(current_user, 'role', 'admin') != 'subadmin'
            or getattr(current_user, 'is_verified', False)
        )
    )
    if admin_count > 0 and not is_verified_admin:
        abort(404)
    public_signup_role = 'admin' if admin_count == 0 else 'subadmin'

    form = AdminSignupForm()
    if is_admin_user:
        form.role.choices = [('admin', 'Admin'), ('subadmin', 'Subadmin')]
    elif admin_count == 0:
        form.role.choices = [('admin', 'Admin')]
    else:
        form.role.choices = [('subadmin', 'Subadmin')]

    if form.validate_on_submit():
        if not is_admin_user and form.role.data != public_signup_role:
            flash('Public signup is only available for subadmins after an admin exists.', 'warning')
            return render_template('admin/signup.html', form=form)

        admin = Admin()
        admin.full_name = (form.full_name.data or '').strip()
        admin.username = (form.username.data or '').strip()
        admin.email = (form.email.data or '').strip().lower()
        admin.is_admin = True
        admin.role = (form.role.data or 'admin').strip().lower()
        admin.is_verified = admin.role != 'subadmin'
        admin.set_password(form.password.data)
        db.session.add(admin)
        db.session.commit()
        flash('Account created successfully. Subadmins need verification before login.' if admin.is_subadmin else 'Admin account created successfully. Please log in.', 'success')
        return redirect(url_for('admin.login'))

    if admin_count > 0 and not is_admin_user:
        flash('Public signup creates subadmin accounts only. Admins can verify them from the dashboard.', 'info')
    return render_template('admin/signup.html', form=form)


@admin_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Start the admin password reset flow via email."""
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = (form.email.data or '').strip().lower()
        admin = Admin.query.filter(func.lower(Admin.email) == email, Admin.is_admin.is_(True)).first()
        if admin:
            token = generate_reset_token(admin)
            reset_url = url_for('admin.reset_password', token=token, _external=True)

            # In local development, allow password reset without SMTP configured.
            # This avoids a noisy error page when MAIL_USERNAME / MAIL_PASSWORD
            # are not set in .env.
            if not _mail_is_configured():
                current_app.logger.info('Mail not configured; generated admin reset link for %s: %s', admin.email, reset_url)
                if current_app.debug:
                    return render_template('admin/forgot_password.html', form=form, reset_link=reset_url, reset_notice='Dev reset link')
                flash('Password reset is temporarily unavailable. Please contact the site owner.', 'warning')
                return render_template('admin/forgot_password.html', form=form, reset_link=reset_url, reset_notice='Password reset is temporarily unavailable')

            try:
                send_reset_email(admin, token)
            except RuntimeError as exc:
                current_app.logger.warning('Admin reset email not sent: %s', exc)
                current_app.logger.info('Admin password reset link for %s: %s', admin.email, reset_url)
                if current_app.debug:
                    flash(f'Dev reset link: {reset_url}', 'info')
                    return render_template('admin/forgot_password.html', form=form)
            except Exception as exc:
                current_app.logger.exception('Failed to send admin reset email: %s', exc)
                flash('Unable to send reset email right now. Please check mail settings.', 'danger')
                return render_template('admin/forgot_password.html', form=form)
        flash('If that email exists, a password reset link has been sent.', 'success')
        return redirect(url_for('admin.login'))
    return render_template('admin/forgot_password.html', form=form)


@admin_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset the admin password using a time-limited token."""
    admin = verify_reset_token(token)
    if not admin:
        flash('That reset link is invalid or has expired.', 'danger')
        return redirect(url_for('admin.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        admin.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated. Please log in.', 'success')
        return redirect(url_for('admin.login'))
    return render_template('admin/reset_password.html', form=form)


# Require login to access logout — performs sign out and redirect home
@admin_bp.route('/logout')
@login_required
def logout():
    """Log out the current admin and redirect to the public homepage."""
    logout_user()
    return redirect(url_for('main.index'))


# -----------------------------
# Admin dashboard
# -----------------------------
@admin_bp.route('/')
@admin_required
def dashboard():
    """Render the admin dashboard with summary statistics.

    - total_bookings: count of Booking records
    - total_rooms: count of Room records
    - available_rooms: rooms with availability flag True
    - recent_bookings: latest bookings for quick review
    """
    total_bookings = Booking.query.count()
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(availability=True).count()
    total_hotels = Hotel.query.count()
    hotel_images = HotelImage.query.count()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    recent_rooms = Room.query.order_by(Room.id.desc()).limit(50).all()
    recent_hotels = Hotel.query.order_by(Hotel.created_at.desc()).limit(10).all()
    pending_subadmins = Admin.query.filter(Admin.role == 'subadmin', Admin.is_verified.is_(False)).order_by(Admin.created_at.desc()).all()
    verified_subadmins = Admin.query.filter(Admin.role == 'subadmin', Admin.is_verified.is_(True)).order_by(Admin.created_at.desc()).all()
    delete_form = DeleteForm()
    # Count enquiries if the file exists
    enquiries_count = 0
    try:
        export_folder = str(current_app.config.get('EXPORT_FOLDER') or os.path.join(current_app.root_path, '..', 'exports'))
        enquiries_path = os.path.join(export_folder, 'enquiries.xlsx')
        if os.path.exists(enquiries_path):
            # Use pandas to count rows (excluding header)
            import pandas as pd
            df = pd.read_excel(enquiries_path)
            enquiries_count = len(df)
    except Exception:
        enquiries_count = 0
    return render_template(
        'admin/dashboard.html',
        total_bookings=total_bookings,
        total_rooms=total_rooms,
        available_rooms=available_rooms,
        total_hotels=total_hotels,
        hotel_images=hotel_images,
        recent_bookings=recent_bookings,
        recent_rooms=recent_rooms,
        recent_hotels=recent_hotels,
        pending_subadmins=pending_subadmins,
        verified_subadmins=verified_subadmins,
        delete_form=delete_form,
        enquiries_count=enquiries_count,
    )


@admin_bp.route('/subadmins/<int:admin_id>/verify', methods=['POST'])
@admin_only
def verify_subadmin(admin_id):
    """Approve a pending subadmin so they can access admin tools."""
    form = DeleteForm()
    if not form.validate_on_submit():
        flash('Invalid verification request.', 'danger')
        return redirect(url_for('admin.dashboard'))

    subadmin = Admin.query.get_or_404(admin_id)
    if getattr(subadmin, 'role', 'admin') != 'subadmin':
        flash('That account is not a subadmin.', 'warning')
        return redirect(url_for('admin.dashboard'))

    subadmin.is_verified = True
    db.session.commit()
    flash(f'Subadmin {subadmin.username} verified successfully.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/subadmins/<int:admin_id>/delete', methods=['POST'])
@admin_only
def delete_subadmin_request(admin_id):
    """Delete a pending subadmin request from the dashboard."""
    form = DeleteForm()
    if not form.validate_on_submit():
        flash('Invalid delete request.', 'danger')
        return redirect(url_for('admin.dashboard'))

    subadmin = Admin.query.get_or_404(admin_id)
    if getattr(subadmin, 'role', 'admin') != 'subadmin':
        flash('That account is not a subadmin request.', 'warning')
        return redirect(url_for('admin.dashboard'))

    if getattr(subadmin, 'is_verified', False):
        flash('Only pending subadmin requests can be deleted from this action.', 'warning')
        return redirect(url_for('admin.dashboard'))

    username = subadmin.username
    db.session.delete(subadmin)
    db.session.commit()
    flash(f'Subadmin request for {username} has been deleted.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/subadmins/<int:admin_id>/remove', methods=['POST'])
@admin_only
def remove_verified_subadmin(admin_id):
    """Remove a verified subadmin account from the dashboard."""
    form = DeleteForm()
    if not form.validate_on_submit():
        flash('Invalid remove request.', 'danger')
        return redirect(url_for('admin.dashboard'))

    subadmin = Admin.query.get_or_404(admin_id)
    if getattr(subadmin, 'role', 'admin') != 'subadmin':
        flash('That account is not a subadmin.', 'warning')
        return redirect(url_for('admin.dashboard'))

    if not getattr(subadmin, 'is_verified', False):
        flash('That subadmin is still pending. Use Delete Request instead.', 'warning')
        return redirect(url_for('admin.dashboard'))

    username = subadmin.username
    db.session.delete(subadmin)
    db.session.commit()
    flash(f'Verified subadmin {username} has been removed.', 'success')
    return redirect(url_for('admin.dashboard'))



@admin_bp.route('/enquiries/download')
@admin_required
def download_enquiries():
    """Allow admin to download the enquiries.xlsx file if present."""
    export_folder = str(current_app.config.get('EXPORT_FOLDER') or os.path.join(current_app.root_path, '..', 'exports'))
    filename = 'enquiries.xlsx'
    filepath = os.path.join(export_folder, filename)
    if not os.path.exists(filepath):
        flash('No enquiries have been collected yet.', 'info')
        return redirect(url_for('admin.dashboard'))
    # send file from export folder
    return send_from_directory(export_folder, filename, as_attachment=True)


# -----------------------------
# Hotel management routes
# -----------------------------
@admin_bp.route('/hotels/add', methods=['GET', 'POST'])
@admin_required
def add_hotel():
    """Create a new hotel listing and upload one or more images."""
    form = HotelForm()
    form.room_id.choices = _room_choices()  # type: ignore[assignment]
    form.room_id.data = form.room_id.data or -1

    if form.validate_on_submit():
        hotel = Hotel()
        hotel.hotel_name = (form.hotel_name.data or '').strip()
        hotel.description = (form.description.data or '').strip()
        hotel.location = (form.location.data or '').strip()
        hotel.price = form.price.data
        hotel.room_type = (form.room_type.data or '').strip()
        hotel.amenities = (form.amenities.data or '').strip()
        hotel.is_available = form.is_available.data
        hotel.room_id = form.room_id.data if form.room_id.data != -1 else None

        upload_folder = current_app.config['HOTEL_UPLOAD_FOLDER']
        image_files = [file for file in (form.images.data or []) if getattr(file, 'filename', '')]
        if not image_files:
            flash('Please upload at least one hotel image (.jpg, .jpeg, .jfif, .png, or .webp).', 'danger')
            return render_template('admin/hotel_form.html', form=form, hotel=None, existing_images=[], delete_form=DeleteForm())

        db.session.add(hotel)
        db.session.flush()

        try:
            saved_urls = save_hotel_images(image_files, upload_folder)
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), 'danger')
            return render_template('admin/hotel_form.html', form=form, hotel=None, existing_images=[], delete_form=DeleteForm())

        for url in saved_urls:
            hotel_image = HotelImage()
            hotel_image.hotel_id = hotel.id
            hotel_image.image_url = url
            db.session.add(hotel_image)

        db.session.commit()
        flash(f'Hotel added successfully. Saved images: {", ".join([url.split("/")[-1] for url in saved_urls])}', 'success')
        return redirect(url_for('admin.edit_hotel', hotel_id=hotel.id))

    # If POST but not validated, log and show errors to help debugging client issues
    if request.method == 'POST' and not form.validate_on_submit():
        current_app.logger.warning('Hotel add form failed validation: %s', form.errors)
        # flatten errors for user-friendly flash
        flat = []
        for field, errs in form.errors.items():
            for e in errs:
                flat.append(f"{field}: {e}")
        if flat:
            flash('Form submission failed: ' + '; '.join(flat), 'danger')

    return render_template('admin/hotel_form.html', form=form, hotel=None, existing_images=[], delete_form=DeleteForm())


@admin_bp.route('/hotels/edit/<int:hotel_id>', methods=['GET', 'POST'])
@admin_required
def edit_hotel(hotel_id):
    """Update an existing hotel and optionally add more images."""
    hotel = Hotel.query.get_or_404(hotel_id)
    form = HotelForm(obj=hotel)
    form.room_id.choices = _room_choices()  # type: ignore[assignment]
    form.room_id.data = hotel.room_id if hotel.room_id is not None else -1

    if form.validate_on_submit():
        hotel.hotel_name = (form.hotel_name.data or '').strip()
        hotel.description = (form.description.data or '').strip()
        hotel.location = (form.location.data or '').strip()
        hotel.price = form.price.data
        hotel.room_type = (form.room_type.data or '').strip()
        hotel.amenities = (form.amenities.data or '').strip()
        hotel.is_available = form.is_available.data
        hotel.room_id = form.room_id.data if form.room_id.data != -1 else None

        upload_folder = current_app.config['HOTEL_UPLOAD_FOLDER']
        image_files = [file for file in (form.images.data or []) if getattr(file, 'filename', '')]
        if image_files:
            try:
                saved_urls = save_hotel_images(image_files, upload_folder)
            except ValueError as exc:
                db.session.rollback()
                flash(str(exc), 'danger')
                return render_template('admin/hotel_form.html', form=form, hotel=hotel, existing_images=hotel.images, delete_form=DeleteForm())

            for url in saved_urls:
                hotel_image = HotelImage()
                hotel_image.hotel_id = hotel.id
                hotel_image.image_url = url
                db.session.add(hotel_image)

        db.session.commit()
        flash('Hotel updated successfully.' + (f' Saved images: {", ".join([url.split("/")[-1] for url in saved_urls])}' if image_files else ''), 'success')
        return redirect(url_for('admin.edit_hotel', hotel_id=hotel.id))

    existing_images = hotel.images
    # If POST but not validated, log errors to console to aid debugging
    if request.method == 'POST' and not form.validate_on_submit():
        current_app.logger.warning('Hotel edit form failed validation for id %s: %s', hotel_id, form.errors)
        flat = []
        for field, errs in form.errors.items():
            for e in errs:
                flat.append(f"{field}: {e}")
        if flat:
            flash('Form submission failed: ' + '; '.join(flat), 'danger')

    return render_template('admin/hotel_form.html', form=form, hotel=hotel, existing_images=existing_images, delete_form=DeleteForm())


@admin_bp.route('/hotels/delete/<int:hotel_id>', methods=['POST'])
@admin_only
def delete_hotel(hotel_id):
    """Delete a hotel and all related uploaded images."""
    form = DeleteForm()
    if not form.validate_on_submit():
        flash('Invalid delete request.', 'danger')
        return redirect(url_for('admin.dashboard'))

    hotel = Hotel.query.get_or_404(hotel_id)
    static_folder = current_app.static_folder
    for image in list(hotel.images):
        delete_hotel_image_file(image.image_url, static_folder)
    db.session.delete(hotel)
    db.session.commit()
    flash('Hotel deleted successfully.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/hotels/images/delete/<int:image_id>', methods=['POST'])
@admin_only
def delete_hotel_image(image_id):
    """Delete a single hotel image from disk and database."""
    form = DeleteForm()
    if not form.validate_on_submit():
        flash('Invalid image delete request.', 'danger')
        return redirect(url_for('admin.dashboard'))

    image = HotelImage.query.get_or_404(image_id)
    delete_hotel_image_file(image.image_url, current_app.static_folder)
    hotel_id = image.hotel_id
    db.session.delete(image)
    db.session.commit()
    flash('Hotel image deleted.', 'success')
    return redirect(url_for('admin.edit_hotel', hotel_id=hotel_id))


@admin_bp.route('/api/hotels', methods=['POST'])
@admin_required
def api_add_hotel():
    """Create a hotel through JSON API input."""
    payload = request.get_json(silent=True) or {}
    required = ['hotel_name', 'description', 'location', 'price', 'room_type', 'amenities']
    missing = [field for field in required if not payload.get(field)]
    if missing:
        return jsonify({'success': False, 'message': f"Missing fields: {', '.join(missing)}"}), 400

    hotel = Hotel()
    hotel.hotel_name = (payload.get('hotel_name') or '').strip()
    hotel.description = (payload.get('description') or '').strip()
    hotel.location = (payload.get('location') or '').strip()
    price_value = payload.get('price') or 0
    hotel.price = float(price_value)
    hotel.room_type = (payload.get('room_type') or '').strip()
    hotel.amenities = (payload.get('amenities') or '').strip()
    hotel.is_available = bool(payload.get('is_available', True))
    hotel.room_id = int(payload['room_id']) if payload.get('room_id') not in (None, '', -1, '-1') else None
    db.session.add(hotel)
    db.session.commit()
    return jsonify({'success': True, 'data': _serialize_hotel(hotel)}), 201


@admin_bp.route('/api/hotels/<int:hotel_id>', methods=['DELETE'])
@admin_only
def api_delete_hotel(hotel_id):
    """Delete a hotel through the admin JSON API."""
    hotel = Hotel.query.get_or_404(hotel_id)
    static_folder = current_app.static_folder
    for image in list(hotel.images):
        delete_hotel_image_file(image.image_url, static_folder)
    db.session.delete(hotel)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Hotel deleted successfully'})


# -----------------------------
# Room creation (management) route
# -----------------------------
@admin_bp.route('/rooms/new', methods=['GET', 'POST'])
@admin_required
def new_room():
    """Create a new room entry.

    - On GET: show `RoomForm` to the admin.
    - On POST: validate form, handle optional image upload, create Room record.
    """
    form = RoomForm()
    if form.validate_on_submit():
        images = None
        f = request.files.get('images')
        if f and f.filename:
            # Securely save uploaded image to UPLOAD_FOLDER
            original_name = secure_filename(f.filename)
            extension = os.path.splitext(original_name)[1].lower()
            filename = f'{uuid.uuid4().hex}{extension}'
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            images = filename
        # Create and persist new room record
        room = Room()
        room.number = form.number.data
        room.room_type = form.room_type.data
        room.price = form.price.data
        room.ac = form.ac.data
        room.availability = form.availability.data
        room.description = form.description.data
        room.images = images
        db.session.add(room)
        db.session.commit()
        flash('Room added', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/room_form.html', form=form, room=None)


@admin_bp.route('/rooms/<int:room_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_room(room_id):
    """Update a room and optionally replace its photo."""
    room = Room.query.get_or_404(room_id)
    form = RoomForm(obj=room)
    if form.validate_on_submit():
        room.number = form.number.data
        room.room_type = form.room_type.data
        room.price = form.price.data
        room.ac = form.ac.data
        room.availability = form.availability.data
        room.description = form.description.data

        f = request.files.get('images')
        if f and f.filename:
            original_name = secure_filename(f.filename)
            extension = os.path.splitext(original_name)[1].lower()
            filename = f'{uuid.uuid4().hex}{extension}'
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            old_image = room.images
            room.images = filename
            _delete_room_image_file(old_image)

        db.session.commit()
        flash('Room updated successfully.', 'success')
        return redirect(url_for('admin.edit_room', room_id=room.id))
    return render_template('admin/room_form.html', form=form, room=room, delete_form=DeleteForm())


@admin_bp.route('/rooms/<int:room_id>/image/delete', methods=['POST'])
@admin_only
def delete_room_image(room_id):
    """Delete only the photo belonging to a room."""
    form = DeleteForm()
    room = Room.query.get_or_404(room_id)
    if not form.validate_on_submit():
        flash('Invalid image delete request.', 'danger')
        return redirect(url_for('admin.edit_room', room_id=room.id))

    _delete_room_image_file(room.images)
    room.images = None
    db.session.commit()
    flash('Room photo deleted.', 'success')
    return redirect(url_for('admin.edit_room', room_id=room.id))


@admin_bp.route('/rooms/<int:room_id>/delete', methods=['POST'])
@admin_only
def delete_room(room_id):
    """Delete a room and its uploaded photo when it has no bookings."""
    form = DeleteForm()
    if not form.validate_on_submit():
        flash('Invalid room delete request.', 'danger')
        return redirect(url_for('admin.dashboard'))

    room = Room.query.get_or_404(room_id)
    if Booking.query.filter_by(room_id=room.id).first():
        flash('This room cannot be deleted because it has existing bookings.', 'warning')
        return redirect(url_for('admin.dashboard'))

    _delete_room_image_file(room.images)
    db.session.delete(room)
    db.session.commit()
    flash('Room deleted successfully.', 'success')
    return redirect(url_for('admin.dashboard'))


# -----------------------------
# Excel upload (preview + process)
# -----------------------------
@admin_bp.route('/excel/preview', methods=['POST'])
@admin_only
def excel_preview_admin():
    """Handle Excel uploads and provide a preview before processing.

    - Save uploaded file to configured upload folder.
    - Use `read_excel_preview` to return a small sample of rows for admin review.
    """
    form = ExcelUploadForm()
    if form.validate_on_submit():
        f = request.files['file']
        filename = secure_filename(f.filename or 'upload.xlsx')
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        f.save(filepath)
        preview = read_excel_preview(filepath)
        return render_template('admin/excel_preview.html', preview=preview, filename=filename)
    flash('Upload failed', 'danger')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/excel/process/<filename>', methods=['POST'])
@admin_only
def excel_process_admin(filename):
    """Process the previously uploaded Excel file and commit changes.

    - Calls `process_excel_upload` which uses pandas/openpyxl to parse and
      insert/update Room and Customer records.
    - Shows a flash message summarizing the result and returns to dashboard.
    """
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(filename))
    result = process_excel_upload(filepath, db.session)
    flash(result.get('message', 'Processed'), 'info')
    return redirect(url_for('admin.dashboard'))
