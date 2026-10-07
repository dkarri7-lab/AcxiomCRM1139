from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from models import db, User, Role
from utils.auth_utils import login_required, role_required, validate_password_policy
from utils.audit_utils import log_audit

user_bp = Blueprint('user', __name__, url_prefix='/users')

@user_bp.route('/')
@login_required
@role_required('Admin')
def index():
    users = User.query.order_by(User.created_date.desc()).all()
    roles = Role.query.all()
    return render_template('users/index.html', users=users, roles=roles)

@user_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role_id = request.form.get('role_id')
        is_active = True if request.form.get('is_active') == 'on' else False

        if not name or not email or not password or not role_id:
            flash('All mandatory user fields must be supplied.', 'danger')
            return render_template('users/create.html', roles=Role.query.all())

        valid_p, msg_p = validate_password_policy(password)
        if not valid_p:
            flash(msg_p, 'danger')
            return render_template('users/create.html', roles=Role.query.all())

        if User.query.filter_by(email=email).first():
            flash('A user with this email address already exists.', 'danger')
            return render_template('users/create.html', roles=Role.query.all())

        role = Role.query.get(role_id)
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role_id=int(role_id),
            is_active=is_active
        )
        db.session.add(user)
        db.session.commit()

        log_audit(action='Create User', entity_name='User', record_id=user.id, new_value=f'Created user {name} ({email}) with role {role.role_name}')
        flash(f'User "{name}" created successfully.', 'success')
        return redirect(url_for('user.index'))

    roles = Role.query.all()
    return render_template('users/create.html', roles=roles)

@user_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit(id):
    user = User.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        role_id = request.form.get('role_id')
        is_active = True if request.form.get('is_active') == 'on' else False
        new_password = request.form.get('new_password', '')

        if not name or not email or not role_id:
            flash('Name, Email and Role are required.', 'danger')
            return render_template('users/edit.html', user=user, roles=Role.query.all())

        existing_user = User.query.filter(User.email == email, User.id != id).first()
        if existing_user:
            flash('Another user is already registered with this email address.', 'danger')
            return render_template('users/edit.html', user=user, roles=Role.query.all())

        old_role = user.role.role_name
        role = Role.query.get(role_id)

        user.name = name
        user.email = email
        user.role_id = int(role_id)
        user.is_active = is_active

        if new_password:
            valid_p, msg_p = validate_password_policy(new_password)
            if not valid_p:
                flash(msg_p, 'danger')
                return render_template('users/edit.html', user=user, roles=Role.query.all())
            user.password_hash = generate_password_hash(new_password)
            log_audit(action='Password Reset', entity_name='User', record_id=user.id, new_value='Admin reset user password')

        db.session.commit()

        log_audit(action='Update User', entity_name='User', record_id=user.id, old_value=f'Role: {old_role}', new_value=f'Role: {role.role_name}, Active: {is_active}')
        flash(f'User "{name}" updated successfully.', 'success')
        return redirect(url_for('user.index'))

    roles = Role.query.all()
    return render_template('users/edit.html', user=user, roles=roles)

@user_bp.route('/<int:id>/unlock', methods=['POST'])
@login_required
@role_required('Admin')
def unlock(id):
    user = User.query.get_or_404(id)
    user.failed_login_count = 0
    user.lockout_until = None
    db.session.commit()

    log_audit(action='Account Unlock', entity_name='User', record_id=user.id, new_value='Admin unlocked user account')
    flash(f'Account for "{user.name}" has been unlocked.', 'success')
    return redirect(url_for('user.index'))
