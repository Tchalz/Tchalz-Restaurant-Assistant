import re
from datetime import datetime

PHONE_PATTERN = re.compile(r"^\+?[0-9\s\-]{7,15}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_date(date_str: str):
    """Returns (is_valid, error_message). Rejects unparsable or past dates."""
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return False, f"'{date_str}' isn't a valid date. Please use YYYY-MM-DD format."
    if parsed < datetime.now().date():
        return False, f"{date_str} is in the past. Please choose a future date."
    return True, ""


def validate_party_size(party_size):
    """Returns (is_valid, error_message). Rejects non-integers and unreasonable sizes."""
    try:
        size = int(party_size)
    except (ValueError, TypeError):
        return False, "Party size must be a whole number."
    if size < 1:
        return False, "Party size must be at least 1."
    if size > 20:
        return False, "For parties larger than 20, please call us directly to arrange group seating."
    return True, ""


def validate_contact(contact: str):
    """Returns (is_valid, error_message). Accepts a phone number or an email address."""
    if not contact or not contact.strip():
        return False, "Please provide a phone number or email address."
    contact = contact.strip()
    if PHONE_PATTERN.match(contact) or EMAIL_PATTERN.match(contact):
        return True, ""
    return False, f"'{contact}' doesn't look like a valid phone number or email address."
