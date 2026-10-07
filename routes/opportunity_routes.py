from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Opportunity, Customer, Lead, User
from utils.auth_utils import login_required, role_required
from utils.validation_utils import validate_opportunity_rules, VALID_OPPORTUNITY_STAGES
from utils.audit_utils import log_audit

opportunity_bp = Blueprint('opportunity', __name__, url_prefix='/opportunities')

@opportunity_bp.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    search_query = request.args.get('search', '').strip()
    stage_filter = request.args.get('stage', '').strip()

    if user_role in ['Admin', 'Manager']:
        query = Opportunity.query
    else:
        query = Opportunity.query.filter_by(owner_id=user_id)

    if search_query:
        query = query.filter(Opportunity.opportunity_name.ilike(f'%{search_query}%'))

    if stage_filter:
        query = query.filter_by(stage=stage_filter)

    opportunities = query.order_by(Opportunity.created_date.desc()).all()
    
    total_pipeline = sum(o.amount for o in opportunities if o.stage not in ['Lost'])
    total_weighted = sum(o.weighted_amount for o in opportunities if o.stage not in ['Lost'])

    return render_template(
        'opportunities/index.html',
        opportunities=opportunities,
        search_query=search_query,
        stage_filter=stage_filter,
        total_pipeline=round(total_pipeline, 2),
        total_weighted=round(total_weighted, 2)
    )

@opportunity_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        opportunity_name = request.form.get('opportunity_name', '').strip()
        customer_id = request.form.get('customer_id')
        amount = request.form.get('amount')
        stage = request.form.get('stage', 'Qualification')
        probability = request.form.get('probability', '20')
        expected_close_date_str = request.form.get('expected_close_date')
        notes = request.form.get('notes', '').strip()
        owner_id = request.form.get('owner_id', session.get('user_id'))

        if not opportunity_name:
            flash('Opportunity Name is required.', 'danger')
            return render_template('opportunities/create.html', customers=Customer.query.all(), sales_execs=User.query.all())

        # Enforce Business Validation Rules
        valid_rules, msg_rules = validate_opportunity_rules(amount, probability, expected_close_date_str, is_active=(stage not in ['Lost']))
        if not valid_rules:
            flash(msg_rules, 'danger')
            return render_template('opportunities/create.html', customers=Customer.query.all(), sales_execs=User.query.all())

        close_date = datetime.strptime(expected_close_date_str, '%Y-%m-%d').date()

        opportunity = Opportunity(
            opportunity_name=opportunity_name,
            customer_id=int(customer_id) if customer_id else None,
            amount=float(amount),
            stage=stage,
            probability=int(probability),
            expected_close_date=close_date,
            notes=notes,
            owner_id=int(owner_id)
        )
        db.session.add(opportunity)
        db.session.commit()

        log_audit(action='Create', entity_name='Opportunity', record_id=opportunity.id, new_value=f'Created Opportunity {opportunity_name}, Amount: ${amount}, Stage: {stage}')
        flash(f'Opportunity "{opportunity_name}" created successfully.', 'success')
        return redirect(url_for('opportunity.index'))

    customers = Customer.query.filter_by(status='Active').all()
    sales_execs = User.query.filter_by(is_active=True).all()
    return render_template('opportunities/create.html', customers=customers, sales_execs=sales_execs)

@opportunity_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    opportunity = Opportunity.query.get_or_404(id)
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if user_role == 'SalesExecutive' and opportunity.owner_id != user_id:
        flash('You are not authorized to edit this opportunity.', 'danger')
        return redirect(url_for('opportunity.index'))

    if request.method == 'POST':
        opportunity_name = request.form.get('opportunity_name', '').strip()
        customer_id = request.form.get('customer_id')
        amount = request.form.get('amount')
        stage = request.form.get('stage', opportunity.stage)
        probability = request.form.get('probability', opportunity.probability)
        expected_close_date_str = request.form.get('expected_close_date')
        notes = request.form.get('notes', '').strip()
        owner_id = request.form.get('owner_id', opportunity.owner_id)

        valid_rules, msg_rules = validate_opportunity_rules(amount, probability, expected_close_date_str, is_active=(stage not in ['Lost']))
        if not valid_rules:
            flash(msg_rules, 'danger')
            return render_template('opportunities/edit.html', opportunity=opportunity, customers=Customer.query.all(), sales_execs=User.query.all())

        close_date = datetime.strptime(expected_close_date_str, '%Y-%m-%d').date()

        old_val = f"Stage: {opportunity.stage}, Amount: ${opportunity.amount}, Prob: {opportunity.probability}%"

        opportunity.opportunity_name = opportunity_name
        opportunity.customer_id = int(customer_id) if customer_id else None
        opportunity.amount = float(amount)
        opportunity.stage = stage
        opportunity.probability = int(probability)
        opportunity.expected_close_date = close_date
        opportunity.notes = notes
        opportunity.owner_id = int(owner_id)

        if stage == 'Won':
            opportunity.status = 'Won'
        elif stage == 'Lost':
            opportunity.status = 'Lost'

        db.session.commit()

        log_audit(action='Update', entity_name='Opportunity', record_id=opportunity.id, old_value=old_val, new_value=f"Stage: {opportunity.stage}, Amount: ${opportunity.amount}, Prob: {opportunity.probability}%")
        flash(f'Opportunity "{opportunity_name}" updated successfully.', 'success')
        return redirect(url_for('opportunity.index'))

    customers = Customer.query.filter_by(status='Active').all()
    sales_execs = User.query.filter_by(is_active=True).all()
    return render_template('opportunities/edit.html', opportunity=opportunity, customers=customers, sales_execs=sales_execs)
