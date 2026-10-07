from flask import request, session
from models import db, AuditLog

def log_audit(action, entity_name=None, record_id=None, old_value=None, new_value=None, user_id=None):
    """
    Appends an immutable audit entry to AuditLog.
    """
    try:
        current_user_id = user_id or session.get('user_id')
        ip_address = request.remote_addr if request else '127.0.0.1'

        audit_entry = AuditLog(
            user_id=current_user_id,
            action=action,
            entity_name=entity_name,
            record_id=str(record_id) if record_id is not None else None,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            ip_address=ip_address
        )
        db.session.add(audit_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error writing audit log: {e}")
