"""Excel utilities for previewing and processing uploaded .xlsx files.

This module uses pandas and openpyxl to read uploaded Excel files and import
data into the Supabase PostgreSQL database. It provides:
- read_excel_preview: returns the first N rows as JSON-like records
- process_excel_upload: basic heuristics to import rooms or customers

Compatible with: PostgreSQL backend (Supabase)
Comments explain the behavior and limitations so maintainers can extend.
"""

import pandas as pd
from openpyxl import load_workbook
from werkzeug.utils import secure_filename
import os


def read_excel_preview(filepath, max_rows=20):
    """Return the first `max_rows` rows of the first sheet as a list of dicts.

    - Uses pandas.read_excel which relies on openpyxl for .xlsx files.
    - Returns {'error': ...} on failure for easy UI handling.
    """
    try:
        df = pd.read_excel(filepath)
        return df.head(max_rows).to_dict(orient='records')
    except Exception as e:
        return {'error': str(e)}


def process_excel_upload(filepath, db_session):
    """Process an uploaded Excel and insert/update DB records.

    - This function uses simple heuristics to detect whether the sheet
      contains Room rows or Customer rows based on header names.
    - It is intentionally conservative: it skips rows missing required keys.
    - Returns a dict with success flag and a message for admin feedback.
    """
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        return {'success': False, 'message': f'Could not read file: {e}'}

    # Normalize header names for detection
    cols = [c.lower() for c in df.columns]
    from app.models import Room, Customer, Booking

    # Detect room import by checking for likely column names
    if 'room' in ' '.join(cols) or 'room_type' in cols or 'number' in cols:
        count = 0
        for _, row in df.iterrows():
            number = str(row.get('number') or row.get('room_number') or row.get('room') or '').strip()
            if not number:
                # Skip rows without a room identifier
                continue
            # Upsert the room by `number`
            room = db_session.query(Room).filter_by(number=number).first()
            if not room:
                room = Room(number=number)
            room.room_type = row.get('room_type') or row.get('type') or room.room_type
            # Guard against missing/NaN price values
            try:
                room.price = float(row.get('price') or room.price or 0)
            except Exception:
                room.price = room.price or 0
            # AC and availability may be stored in different formats; keep existing when unclear
            room.ac = bool(row.get('ac') if 'ac' in row else room.ac)
            room.availability = bool(row.get('availability') if 'availability' in row else room.availability)
            room.description = row.get('description') or room.description
            db_session.add(room)
            count += 1
        db_session.commit()
        return {'success': True, 'message': f'{count} rooms processed'}

    # Detect customer import by presence of name and phone/email
    if 'customer' in ' '.join(cols) or ('name' in cols and ('phone' in cols or 'email' in cols)):
        count = 0
        for _, row in df.iterrows():
            name = row.get('name')
            if not name:
                continue
            customer = db_session.query(Customer).filter_by(name=name).first()
            if not customer:
                customer = Customer(name=name)
            customer.email = row.get('email') or customer.email
            customer.phone = row.get('phone') or customer.phone
            db_session.add(customer)
            count += 1
        db_session.commit()
        return {'success': True, 'message': f'{count} customers processed'}

    # If headers don't match expected patterns, return an informative message
    return {'success': False, 'message': 'No recognized data headers. Expected rooms or customers.'}

