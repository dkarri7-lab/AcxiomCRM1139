from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, FollowUp, Customer, Lead, User
from utils.auth_utils import login_required, role_required
from utils.validation_utils import validate_followup_rules
from utils.audit_utils import log_audit

followup_bp = Blueprint('followup', __name__, url_prefix='/followups')

@followup_bp.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    status_filter = request.args.get('status', '').strip()

    if user_role in ['Admin', 'Manager']:
        query = FollowUp.query
    else:
        query = FollowUp.query.filter_by(assigned_to=user_id)

    if status_filter:
        query = query.filter_by(status=status_filter)

    followups = query.order_by(FollowUp.followup_date.asc()).all()
    today = datetime.utcnow()

    return render_template('followups/index.html', followups=followups, status_filter=status_filter, today=today)

@followup_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        followup_date_str = request.form.get('followup_date')
        followup_type = request.form.get('followup_type', 'Call')
        customer_id = request.form.get('customer_id')
        lead_id = request.form.get('lead_id')
        assigned_to = request.form.get('assigned_to', session.get('user_id'))
        remarks = request.form.get('remarks', '').strip()

        if not subject:
            flash('Subject is required for a follow-up.', 'danger')
            return render_template('followups/create.html', customers=Customer.query.all(), leads=Lead.query.all(), sales_execs=User.query.all())

        # Mandatory Business Validation Rule
        valid_rules, msg_rules = validate_followup_rules(followup_date_str, status='Planned')
        if not valid_rules:
            flash(msg_rules, 'danger')
            return render_template('followups/create.html', customers=Customer.query.all(), leads=Lead.query.all(), sales_execs=User.query.all())

        # Parse DateTime
        if 'T' in followup_date_str:
            f_dt = datetime.strptime(followup_date_str, '%Y-%m-%dT%H:%M')
        else:
            f_dt = datetime.strptime(followup_date_str, '%Y-%m-%d')

        followup = FollowUp(
            subject=subject,
            followup_date=f_dt,
            followup_type=followup_type,
            customer_id=int(customer_id) if customer_id else None,
            lead_id=int(lead_id) if lead_id else None,
            assigned_to=int(assigned_to),
            remarks=remarks,
            status='Planned'
        )
        db.session.add(followup)
        db.session.commit()

        log_audit(action='Create', entity_name='FollowUp', record_id=followup.id, new_value=f'Scheduled FollowUp "{subject}" on {f_dt.strftime("%Y-%m-%d %H:%M")}')
        flash(f'Follow-up "{subject}" scheduled successfully.', 'success')
        return redirect(url_for('followup.index'))

    customers = Customer.query.filter_by(status='Active').all()
    leads = Lead.query.filter(Lead.status.notin_(['Converted', 'Lost'])).all()
    sales_execs = User.query.filter_by(is_active=True).all()

    return render_template('followups/create.html', customers=customers, leads=leads, sales_execs=sales_execs)

@followup_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    followup = FollowUp.query.get_or_404(id)
    new_status = request.form.get('status', 'Completed')

    old_status = followup.status
    followup.status = new_status
    db.session.commit()

    log_audit(action='Update Status', entity_name='FollowUp', record_id=followup.id, old_value=f'Status: {old_status}', new_value=f'Status: {new_status}')
    flash(f'Follow-up status changed to "{new_status}".', 'success')
    return redirect(url_for('followup.index'))
