from flask import Blueprint, render_template, request, session
from models import db, AuditLog, User
from utils.auth_utils import login_required, role_required

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

@audit_bp.route('/')
@login_required
@role_required('Admin', 'Manager')
def index():
    user_filter = request.args.get('user_id', '')
    entity_filter = request.args.get('entity', '').strip()
    action_filter = request.args.get('action', '').strip()

    query = AuditLog.query

    if user_filter:
        query = query.filter_by(user_id=int(user_filter))
    if entity_filter:
        query = query.filter_by(entity_name=entity_filter)
    if action_filter:
        query = query.filter_by(action=action_filter)

    audit_logs = query.order_by(AuditLog.created_date.desc()).limit(200).all()
    users = User.query.all()

    return render_template(
        'audit/index.html',
        audit_logs=audit_logs,
        users=users,
        user_filter=user_filter,
        entity_filter=entity_filter,
        action_filter=action_filter
    )
