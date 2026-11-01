"""Main blueprint routes with Supabase PostgreSQL backend.

Public routes include dynamic hotel listings, hotel detail pages, room detail
pages, and customer booking flows. The admin blueprint handles mutations.
"""
from flask import abort, render_template, request, redirect, url_for, flash, current_app, send_from_directory, jsonify, Response
from flask_login import current_user
from werkzeug.utils import secure_filename
import os
from app.routes import main_bp
from app.routes.admin import admin_required
from app import db
from app.models import Room, Customer, Booking, Hotel
from app.forms import BookingForm, ExcelUploadForm
from app.services.excel_utils import read_excel_preview, process_excel_upload
from app.services.enquiry_utils import append_enquiry, ensure_enquiry_file_exists
from datetime import date
import json


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


# -----------------------------
# Home / Landing page
# -----------------------------
@main_bp.route('/')
def index():
    """Render homepage with featured hotels and rooms."""
    hotels = Hotel.query.order_by(Hotel.created_at.desc()).limit(6).all()
    room_section_hotels = Hotel.query.order_by(Hotel.created_at.desc()).all()
    rooms = Room.query.limit(6).all()
    gallery_images = [image.image_url for hotel in hotels for image in hotel.images][:6]
    return render_template('index.html', hotels=hotels, room_section_hotels=room_section_hotels, rooms=rooms, gallery_images=gallery_images)


@main_bp.route('/health')
def health():
    """Lightweight readiness endpoint for load balancers and monitoring."""
    return jsonify({'status': 'ok'})


@main_bp.route('/hotels')
def hotels():
    """Dedicated public page showing all hotel listings."""
    hotels = Hotel.query.order_by(Hotel.created_at.desc()).all()
    room_section_hotels = hotels
    rooms = Room.query.limit(6).all()
    gallery_images = [image.image_url for hotel in hotels for image in hotel.images][:6]
    return render_template('index.html', hotels=hotels, room_section_hotels=room_section_hotels, rooms=rooms, gallery_images=gallery_images)


@main_bp.route('/hotel/<int:hotel_id>')
def hotel_detail(hotel_id):
    """Show detailed information for a single hotel listing."""
    hotel = Hotel.query.get_or_404(hotel_id)
    linked_room = Room.query.get(hotel.room_id) if hotel.room_id else None
    return render_template('hotel_detail.html', hotel=hotel, linked_room=linked_room)


# -----------------------------
# Room detail page
# -----------------------------
@main_bp.route('/room/<int:room_id>')
def room_detail(room_id):
    """Show detailed information for a single room.

    - Fetch the room by ID or return 404 if not found.
    - Renders `room_detail.html` including images and booking CTA.
    """
    room = Room.query.get_or_404(room_id)
    return render_template('room_detail.html', room=room)


# -----------------------------
# Booking endpoint (user-facing)
# -----------------------------
@main_bp.route('/book/<int:room_id>', methods=['GET', 'POST'])
def book(room_id):
    """Allow customers to create a booking for a specific room.

    - GET: show booking form pre-filled for the selected room.
    - POST: validate the booking form, create Customer and Booking records.
    - NOTE: Payment handling is kept as 'pay later' placeholder here.
    """
    room = Room.query.get_or_404(room_id)
    form = BookingForm()
    if form.validate_on_submit():
        # Create customer record and commit so we have an ID
        customer = Customer()
        customer.name = form.name.data
        customer.email = form.email.data
        customer.phone = form.phone.data
        db.session.add(customer)
        db.session.commit()

        # Create booking linked to the room and customer
        booking = Booking()
        booking.room_id = room.id
        booking.customer_id = customer.id
        booking.check_in = form.check_in.data
        booking.check_out = form.check_out.data
        booking.total_price = room.price
        db.session.add(booking)
        db.session.commit()
        flash('Booking confirmed', 'success')
        return redirect(url_for('main.index'))

    # Render booking form
    return render_template('book.html', room=room, form=form)


# -----------------------------
# Hotel JSON APIs (public read endpoints)
# -----------------------------
@main_bp.route('/api/hotels')
def api_hotels():
    """Return all hotels as JSON for frontend consumers."""
    hotels = Hotel.query.order_by(Hotel.created_at.desc()).all()
    return jsonify({'success': True, 'data': [_serialize_hotel(hotel) for hotel in hotels]})


@main_bp.route('/api/hotels/<int:hotel_id>')
def api_hotel_detail(hotel_id):
    """Return one hotel and its images as JSON."""
    hotel = Hotel.query.get_or_404(hotel_id)
    return jsonify({'success': True, 'data': _serialize_hotel(hotel)})


@main_bp.route('/api/hotels/<int:hotel_id>/images')
def api_hotel_images(hotel_id):
    """Return only the image URLs for a hotel."""
    hotel = Hotel.query.get_or_404(hotel_id)
    return jsonify({'success': True, 'data': [{'id': image.id, 'image_url': image.image_url} for image in hotel.images]})


# -----------------------------
# Browser/devtools probes
# -----------------------------
@main_bp.route('/.well-known/appspecific/com.chrome.devtools.json')
def chrome_devtools_probe():
    """Respond to Chrome DevTools' local probe without logging a 404."""
    return jsonify({})


# -----------------------------
# Static uploads helper
# -----------------------------
@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files (images, excel previews) from UPLOAD_FOLDER.

    - This is a simple helper used during development. In production,
      use a proper static file server or CDN.
    """
    safe_filename = secure_filename(filename)
    extension = os.path.splitext(safe_filename)[1].lower().lstrip('.')
    public_extensions = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
    is_verified_admin = (
        current_user.is_authenticated
        and getattr(current_user, 'is_admin', False)
        and (
            getattr(current_user, 'role', 'admin') != 'subadmin'
            or getattr(current_user, 'is_verified', False)
        )
    )
    if extension not in public_extensions and not is_verified_admin:
        abort(404)
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], safe_filename)


# -----------------------------
# Excel preview/process (minimal admin flows)
# -----------------------------
@main_bp.route('/admin/excel/preview', methods=['POST'])
@admin_required
def excel_preview():
    """Accept an uploaded Excel file and show a small preview.

    - Saves the uploaded file to UPLOAD_FOLDER.
    - Uses `read_excel_preview` to return first N rows for admin validation.
    - This endpoint is intentionally lightweight and should be protected by
      admin authentication in production (it's used here for demo purposes).
    """
    form = ExcelUploadForm()
    if form.validate_on_submit():
        f = request.files['file']
        filename = secure_filename(f.filename or 'upload.xlsx')
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        f.save(filepath)
        preview = read_excel_preview(filepath)
        return render_template('excel_preview.html', preview=preview, filename=filename)
    flash('File upload failed', 'danger')
    return redirect(url_for('main.index'))


@main_bp.route('/admin/excel/process/<filename>', methods=['POST'])
@admin_required
def excel_process(filename):
    """Process an uploaded Excel file and import rows into the database.

    - Calls `process_excel_upload` which contains simple heuristics to detect
      rooms or customers and insert/update records.
    - Shows a flash message with the result and redirects back to home.
    """
    upload_folder = str(current_app.config.get('UPLOAD_FOLDER') or os.path.join(current_app.root_path, '..', 'uploads'))
    filepath = os.path.join(upload_folder, secure_filename(filename))
    result = process_excel_upload(filepath, db.session)
    flash(result.get('message', 'Processed'), 'info')
    return redirect(url_for('main.index'))


# -----------------------------
# Customer enquiry endpoint
# -----------------------------
@main_bp.route('/enquire', methods=['POST'])
def enquire():
    """Accept AJAX enquiries and persist them into an Excel file (no DB).

    Expects JSON: {name: str, phone: str}
    Returns JSON {success: bool, message: str}
    """
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    phone = (data.get('phone') or '').strip()

    # Basic validation
    if not name:
        return jsonify({'success': False, 'message': 'Name is required.'}), 400
    digits = ''.join(ch for ch in phone if ch.isdigit())
    if len(digits) < 7 or len(digits) > 15:
        return jsonify({'success': False, 'message': 'Please enter a valid phone number.'}), 400

    export_folder = str(current_app.config.get('EXPORT_FOLDER') or os.path.join(current_app.root_path, '..', 'exports'))
    filepath = os.path.join(export_folder, 'enquiries.xlsx')

    ensure_enquiry_file_exists(filepath)
    result = append_enquiry(filepath, name, phone)
    if not result.get('success'):
        return jsonify({'success': False, 'message': 'Could not save enquiry: ' + result.get('message', '')}), 500

    return jsonify({'success': True, 'message': 'Thank you — your enquiry was received.'})


# -----------------------------
# SEO: sitemap.xml and robots.txt
# -----------------------------
SITE_URL = "https://hotelstayinujjain.com"


@main_bp.route('/sitemap.xml')
def sitemap():
    """Generate a sitemap of all public pages, including every hotel and room."""
    paths = ['/', '/hotels']
    paths += [f'/hotel/{h.id}' for h in Hotel.query.all()]
    paths += [f'/room/{r.id}' for r in Room.query.all()]
    urls = ''.join(f'<url><loc>{SITE_URL}{p}</loc></url>' for p in paths)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           f'{urls}</urlset>')
    return Response(xml, mimetype='application/xml')


@main_bp.route('/robots.txt')
def robots():
    """Tell crawlers what to skip and where the sitemap is."""
    txt = f"User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\nSitemap: {SITE_URL}/sitemap.xml\n"
    return Response(txt, mimetype='text/plain')