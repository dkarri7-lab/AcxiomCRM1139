import re
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Role

def validate_password_policy(password):
    """
    Password Policy Requirements:
    - At least 8 characters long
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        return False, "Password must contain at least one special character (!@#$%^&*)."
    return True, "Password meets complexity requirements."

def is_account_locked(user):
    if user.lockout_until:
        if datetime.utcnow() < user.lockout_until:
            return True, f"Account is locked due to repeated failed login attempts. Try again after {user.lockout_until.strftime('%H:%M:%S UTC')}."
        else:
            # Lockout expired, reset
            user.lockout_until = None
            user.failed_login_count = 0
            db.session.commit()
    return False, None

def record_failed_login(user):
    user.failed_login_count += 1
    if user.failed_login_count >= 5:
        user.lockout_until = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()
        return True, "Account locked! Maximum failed attempts (5) reached. Account locked for 15 minutes."
    db.session.commit()
    return False, f"Invalid credentials. Attempt {user.failed_login_count} of 5 before lockout."

def reset_failed_login(user):
    user.failed_login_count = 0
    user.lockout_until = None
    db.session.commit()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
                return redirect(url_for('auth.login'))
            
            user_role = session.get('user_role')
            if user_role not in roles:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Forbidden', 'message': f'Access restricted to roles: {", ".join(roles)}'}), 403
                flash(f'Access denied. Required role: {", ".join(roles)}', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
