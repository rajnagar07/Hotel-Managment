"""Utilities for storing customer enquiries into an Excel file.

This module uses openpyxl for low-level workbook inspection and appending
rows, and pandas for initial file creation when needed. It enforces the
business rule that the Date column is written only once per day: the first
enquiry of a day will include the date, subsequent enquiries on the same day
will have the Date cell empty.

Functions:
- ensure_enquiry_file_exists(path)
- append_enquiry(path, name, phone)
"""
from datetime import date
import os
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
import pandas as pd


def ensure_enquiry_file_exists(path: str):
    """Create the enquiries.xlsx file with headers if it does not exist."""
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    if not os.path.exists(path):
        # Create with pandas for a clean header row
        df = pd.DataFrame(columns=['Name', 'Phone Number', 'Date'])
        df.to_excel(path, index=False, engine='openpyxl')


def _last_written_date(path: str):
    """Return the last non-empty date string found in the Date column (column C) or None."""
    try:
        wb = load_workbook(filename=path, read_only=True, data_only=True)
        ws = wb.active
        # Date is expected in column C (3)
        col = 3
        # iterate from bottom to top looking for first non-empty value
        for row in range(ws.max_row, 0, -1):
            cell = ws.cell(row=row, column=col)
            if cell.value is None:
                continue
            # normalize to ISO date string if possible
            if isinstance(cell.value, (str,)) and str(cell.value).strip() == '':
                continue
            val = cell.value
            try:
                # if it's a date object
                if hasattr(val, 'isoformat'):
                    return val.isoformat()
            except Exception:
                pass
            return str(val)
    except FileNotFoundError:
        return None
    except Exception:
        return None


def append_enquiry(path: str, name: str, phone: str) -> dict:
    """Append an enquiry to the Excel file.

    Returns a dict {'success': bool, 'message': str}
    """
    try:
        ensure_enquiry_file_exists(path)

        last_date = _last_written_date(path)
        today = date.today().isoformat()

        # Determine the date value for this row: only write date when last_date != today
        date_to_write = today if (last_date is None or str(last_date) != today) else ''

        # Use openpyxl to append a new row for minimal overhead
        wb = load_workbook(filename=path)
        ws = wb.active
        ws.append([name, phone, date_to_write])
        wb.save(path)
        return {'success': True, 'message': 'Enquiry saved'}
    except Exception as exc:
        return {'success': False, 'message': str(exc)}
