import uuid
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Lead, Customer, Opportunity, User
from utils.auth_utils import login_required, role_required
from utils.validation_utils import validate_email, validate_phone, validate_lead_rules, VALID_LEAD_STATUSES
from utils.audit_utils import log_audit

lead_bp = Blueprint('lead', __name__, url_prefix='/leads')

@lead_bp.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()

    if user_role in ['Admin', 'Manager']:
        query = Lead.query
    else:
        query = Lead.query.filter_by(owner_id=user_id)

    if search_query:
        query = query.filter(
            (Lead.lead_name.ilike(f'%{search_query}%')) |
            (Lead.email.ilike(f'%{search_query}%')) |
            (Lead.company_name.ilike(f'%{search_query}%'))
        )

    if status_filter:
        query = query.filter_by(status=status_filter)

    leads = query.order_by(Lead.created_date.desc()).all()
    return render_template('leads/index.html', leads=leads, search_query=search_query, status_filter=status_filter)

@lead_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        lead_name = request.form.get('lead_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        company_name = request.form.get('company_name', '').strip()
        source = request.form.get('source', 'Web')
        status = request.form.get('status', 'New')
        priority = request.form.get('priority', 'Medium')
        expected_value = request.form.get('expected_value', '0')
        owner_id = request.form.get('owner_id', session.get('user_id'))

        # Validations
        valid_rules, msg_rules = validate_lead_rules(lead_name, status, expected_value)
        if not valid_rules:
            flash(msg_rules, 'danger')
            return render_template('leads/create.html', sales_execs=User.query.all())

        valid_e, msg_e = validate_email(email)
        if not valid_e:
            flash(msg_e, 'danger')
            return render_template('leads/create.html', sales_execs=User.query.all())

        valid_p, msg_p = validate_phone(phone)
        if not valid_p:
            flash(msg_p, 'danger')
            return render_template('leads/create.html', sales_execs=User.query.all())

        lead_code = f"LEAD-{uuid.uuid4().hex[:6].upper()}"

        lead = Lead(
            lead_code=lead_code,
            lead_name=lead_name,
            email=email,
            phone=phone,
            company_name=company_name,
            source=source,
            status=status,
            priority=priority,
            expected_value=float(expected_value),
            owner_id=int(owner_id)
        )
        db.session.add(lead)
        db.session.commit()

        log_audit(action='Create', entity_name='Lead', record_id=lead.id, new_value=f'Created Lead {lead_name} ({lead_code})')
        flash(f'Lead "{lead_name}" created successfully.', 'success')
        return redirect(url_for('lead.index'))

    sales_execs = User.query.filter_by(is_active=True).all()
    return render_template('leads/create.html', sales_execs=sales_execs)

@lead_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    lead = Lead.query.get_or_404(id)
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if user_role == 'SalesExecutive' and lead.owner_id != user_id:
        flash('You are not authorized to edit this lead.', 'danger')
        return redirect(url_for('lead.index'))

    if request.method == 'POST':
        lead_name = request.form.get('lead_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        company_name = request.form.get('company_name', '').strip()
        source = request.form.get('source', lead.source)
        status = request.form.get('status', lead.status)
        priority = request.form.get('priority', lead.priority)
        expected_value = request.form.get('expected_value', lead.expected_value)
        owner_id = request.form.get('owner_id', lead.owner_id)

        valid_rules, msg_rules = validate_lead_rules(lead_name, status, expected_value)
        if not valid_rules:
            flash(msg_rules, 'danger')
            return render_template('leads/edit.html', lead=lead, sales_execs=User.query.all())

        valid_e, msg_e = validate_email(email)
        if not valid_e:
            flash(msg_e, 'danger')
            return render_template('leads/edit.html', lead=lead, sales_execs=User.query.all())

        valid_p, msg_p = validate_phone(phone)
        if not valid_p:
            flash(msg_p, 'danger')
            return render_template('leads/edit.html', lead=lead, sales_execs=User.query.all())

        old_val = f"Status: {lead.status}, Value: {lead.expected_value}"

        lead.lead_name = lead_name
        lead.email = email
        lead.phone = phone
        lead.company_name = company_name
        lead.source = source
        lead.status = status
        lead.priority = priority
        lead.expected_value = float(expected_value)
        lead.owner_id = int(owner_id)

        db.session.commit()

        log_audit(action='Update', entity_name='Lead', record_id=lead.id, old_value=old_val, new_value=f"Status: {lead.status}, Value: {lead.expected_value}")
        flash(f'Lead "{lead_name}" updated successfully.', 'success')
        return redirect(url_for('lead.index'))

    sales_execs = User.query.filter_by(is_active=True).all()
    return render_template('leads/edit.html', lead=lead, sales_execs=sales_execs)

@lead_bp.route('/<int:id>/convert', methods=['GET', 'POST'])
@login_required
def convert(id):
    """
    Mandatory Workflow: Lead Conversion into Customer & Opportunity
    """
    lead = Lead.query.get_or_404(id)

    if lead.status == 'Converted':
        flash('This lead has already been converted into a customer.', 'warning')
        return redirect(url_for('lead.index'))

    if request.method == 'POST':
        opp_name = request.form.get('opportunity_name', f"{lead.company_name or lead.lead_name} Deal").strip()
        amount = request.form.get('amount', lead.expected_value)
        close_date_str = request.form.get('expected_close_date')

        # Create new Customer from Lead if not existing
        existing_cust = Customer.query.filter((Customer.email == lead.email) | (Customer.phone == lead.phone)).first()
        if not existing_cust:
            cust_code = f"CUST-{uuid.uuid4().hex[:6].upper()}"
            customer = Customer(
                customer_code=cust_code,
                customer_name=lead.lead_name,
                email=lead.email,
                phone=lead.phone,
                company_name=lead.company_name,
                owner_id=lead.owner_id,
                created_by=session.get('user_name')
            )
            db.session.add(customer)
            db.session.flush() # get customer.id
        else:
            customer = existing_cust

        # Create Opportunity
        close_date = datetime.strptime(close_date_str, '%Y-%m-%d').date() if close_date_str else date.today()
        opportunity = Opportunity(
            opportunity_name=opp_name,
            customer_id=customer.id,
            lead_id=lead.id,
            amount=float(amount),
            stage='Qualification',
            probability=20,
            expected_close_date=close_date,
            owner_id=lead.owner_id
        )
        db.session.add(opportunity)

        # Update Lead status to Converted
        lead.status = 'Converted'
        db.session.commit()

        log_audit(
            action='Lead Conversion',
            entity_name='Lead',
            record_id=lead.id,
            old_value=f'Status: Qualified',
            new_value=f'Converted to Customer ID: {customer.id}, Opportunity ID: {opportunity.id}'
        )

        flash(f'Lead "{lead.lead_name}" converted into Customer & Opportunity successfully!', 'success')
        return redirect(url_for('customer.details', id=customer.id))

    return render_template('leads/convert.html', lead=lead)
