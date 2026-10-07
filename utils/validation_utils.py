import re
from datetime import datetime, date

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PHONE_REGEX = r'^[0-9\+\-\s\(\)]{7,20}$' # 7 to 20 digits, supports Indian format and international

VALID_LEAD_STATUSES = {'New', 'Contacted', 'Qualified', 'Unqualified', 'Converted', 'Lost'}
VALID_OPPORTUNITY_STAGES = {'Qualification', 'Proposal', 'Negotiation', 'Won', 'Lost'}
VALID_FOLLOWUP_STATUSES = {'Planned', 'Completed', 'Missed', 'Cancelled'}

def validate_email(email):
    if not email:
        return False, "Email address is required."
    if not re.match(EMAIL_REGEX, email):
        return False, "Enter a valid email address (e.g. user@example.com)."
    return True, None

def validate_phone(phone):
    if not phone:
        return False, "Phone number is required."
    if not re.match(PHONE_REGEX, phone):
        return False, "Enter a valid phone number (e.g., 10-digit mobile number)."
    return True, None

def validate_opportunity_rules(amount, probability, expected_close_date_str, is_active=True):
    """
    Mandatory Business Rules for Opportunities:
    - Opportunity Amount must be > 0.
    - Probability must be between 0 and 100 inclusive.
    - Expected Close Date cannot be in the past for active opportunities.
    """
    # 1. Amount
    try:
        val_amount = float(amount)
        if is_active and val_amount <= 0:
            return False, "Opportunity Amount must be greater than 0."
    except (ValueError, TypeError):
        return False, "Opportunity Amount must be a valid numeric value."

    # 2. Probability
    try:
        val_prob = int(probability)
        if val_prob < 0 or val_prob > 100:
            return False, "Probability must be between 0 and 100."
    except (ValueError, TypeError):
        return False, "Probability must be a whole number between 0 and 100."

    # 3. Expected Close Date
    try:
        if isinstance(expected_close_date_str, str):
            close_date = datetime.strptime(expected_close_date_str, '%Y-%m-%d').date()
        elif isinstance(expected_close_date_str, (datetime, date)):
            close_date = expected_close_date_str if isinstance(expected_close_date_str, date) else expected_close_date_str.date()
        else:
            return False, "Invalid expected close date format."
            
        today = date.today()
        if is_active and close_date < today:
            return False, "Expected Close Date cannot be in the past."
    except ValueError:
        return False, "Expected Close Date must be in YYYY-MM-DD format."

    return True, None

def validate_followup_rules(followup_date_str, status='Planned'):
    """
    Mandatory Business Rules for Follow-Ups:
    - Follow-Up Date cannot be earlier than today for new/planned follow-ups.
    """
    try:
        if isinstance(followup_date_str, str):
            # Accept date or datetime string
            if 'T' in followup_date_str:
                f_date = datetime.strptime(followup_date_str, '%Y-%m-%dT%H:%M').date()
            elif ' ' in followup_date_str:
                f_date = datetime.strptime(followup_date_str, '%Y-%m-%d %H:%M').date()
            else:
                f_date = datetime.strptime(followup_date_str, '%Y-%m-%d').date()
        elif isinstance(followup_date_str, (datetime, date)):
            f_date = followup_date_str if isinstance(followup_date_str, date) else followup_date_str.date()
        else:
            return False, "Invalid follow-up date."

        today = date.today()
        if status in ['Planned', 'New'] and f_date < today:
            return False, "Follow-up date cannot be earlier than today."
    except ValueError:
        return False, "Invalid follow-up date format."

    return True, None

def validate_lead_rules(name, status, expected_value=0):
    if not name or len(name.strip()) == 0:
        return False, "Lead name is mandatory."
    if status not in VALID_LEAD_STATUSES:
        return False, f"Invalid lead status. Allowed statuses: {', '.join(VALID_LEAD_STATUSES)}."
    try:
        val_exp = float(expected_value)
        if val_exp < 0:
            return False, "Expected value cannot be negative."
    except (ValueError, TypeError):
        return False, "Expected value must be a valid number."

    return True, None
