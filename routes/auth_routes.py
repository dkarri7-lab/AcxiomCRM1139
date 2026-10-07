from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Role
from utils.auth_utils import validate_password_policy, is_account_locked, record_failed_login, reset_failed_login
from utils.audit_utils import log_audit

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if not user:
            log_audit(action='Login Failure', entity_name='User', old_value=f'Unknown Email: {email}')
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            log_audit(action='Login Failure', entity_name='User', record_id=user.id, old_value='Inactive Account Attempt', user_id=user.id)
            flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            return render_template('auth/login.html')

        # Check Account Lockout State
        locked, lock_message = is_account_locked(user)
        if locked:
            log_audit(action='Login Locked Attempt', entity_name='User', record_id=user.id, old_value=lock_message, user_id=user.id)
            flash(lock_message, 'danger')
            return render_template('auth/login.html')

        # Check Password Hash
        if check_password_hash(user.password_hash, password):
            reset_failed_login(user)
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            session['user_role'] = user.role.role_name if user.role else 'SalesExecutive'

            log_audit(action='Login', entity_name='User', record_id=user.id, new_value=f'Successful Login as {user.role.role_name}', user_id=user.id)
            flash(f'Welcome back, {user.name}!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            is_now_locked, lock_msg = record_failed_login(user)
            log_audit(action='Login Failure', entity_name='User', record_id=user.id, old_value=f'Failed Attempts: {user.failed_login_count}', user_id=user.id)
            flash(lock_msg, 'danger')
            return render_template('auth/login.html')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role_name = request.form.get('role_name', 'SalesExecutive')

        if not name or not email or not password:
            flash('All fields are mandatory.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        # Validate Password Policy
        valid_policy, policy_msg = validate_password_policy(password)
        if not valid_policy:
            flash(policy_msg, 'danger')
            return render_template('auth/register.html')

        # Check Email Uniqueness
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/register.html')

        role = Role.query.filter_by(role_name=role_name).first()
        if not role:
            role = Role.query.filter_by(role_name='SalesExecutive').first()

        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role_id=role.id,
            is_active=True
        )
        db.session.add(new_user)
        db.session.commit()

        log_audit(action='User Registration', entity_name='User', record_id=new_user.id, new_value=f'Registered {email} with role {role.role_name}', user_id=new_user.id)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    roles = Role.query.all()
    return render_template('auth/register.html', roles=roles)

@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        log_audit(action='Logout', entity_name='User', record_id=user_id, user_id=user_id)
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))
