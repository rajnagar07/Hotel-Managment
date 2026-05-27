"""Hotel image utilities for admin uploads.

Provides secure filename generation, file type validation, and cleanup helpers
for hotel image management stored under `static/uploads/hotels/`.
"""

import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'jfif', 'png', 'webp'}


def allowed_hotel_image(filename):
    """Return True when the filename has an allowed image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def _normalized_static_path(path):
    return path.replace('\\', '/').lstrip('/')


def save_hotel_images(files, upload_folder, static_prefix='static'):
    """Validate and save uploaded files, returning a list of relative URLs.

    The returned values are paths like `/static/uploads/hotels/<uuid>.png`.
    """
    os.makedirs(upload_folder, exist_ok=True)
    saved = []
    for file in files or []:
        if not file or not file.filename:
            continue
        original = secure_filename(file.filename)
        if not allowed_hotel_image(original):
            raise ValueError(f'Unsupported image type for file: {original}')
        ext = original.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        saved.append(f"/{_normalized_static_path(os.path.join(static_prefix, 'uploads', 'hotels', filename))}")
    return saved


def delete_hotel_image_file(image_url, static_folder):
    """Delete a hotel image file from disk when the DB record is removed."""
    if not image_url:
        return
    relative = image_url.lstrip('/').replace('/', os.sep)
    if relative.startswith('static' + os.sep):
        path = os.path.join(static_folder, relative[len('static' + os.sep):])
        if os.path.exists(path):
            os.remove(path)