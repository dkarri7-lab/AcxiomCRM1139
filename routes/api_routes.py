import uuid
from datetime import datetime, date
from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash
from models import db, User, Customer, Lead, Opportunity, FollowUp
from utils.auth_utils import login_required, role_required, is_account_locked, record_failed_login, reset_failed_login
from utils.validation_utils import validate_email, validate_phone, validate_opportunity_rules, validate_followup_rules, validate_lead_rules
from utils.audit_utils import log_audit

api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- AUTH API ---
@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Bad Request', 'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Forbidden', 'message': 'Account deactivated'}), 403

    locked, lock_msg = is_account_locked(user)
    if locked:
        return jsonify({'error': 'Locked', 'message': lock_msg}), 423

    if check_password_hash(user.password_hash, password):
        reset_failed_login(user)
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        session['user_role'] = user.role.role_name

        log_audit(action='API Login', entity_name='User', record_id=user.id, user_id=user.id)
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200
    else:
        record_failed_login(user)
        return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401

@api_bp.route('/auth/logout', methods=['POST'])
@login_required
def api_logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

# --- CUSTOMER REST API ---
@api_bp.route('/customers', methods=['GET'])
@login_required
def api_get_customers():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if user_role in ['Admin', 'Manager']:
        customers = Customer.query.all()
    else:
        customers = Customer.query.filter_by(owner_id=user_id).all()

    return jsonify([c.to_dict() for c in customers]), 200

@api_bp.route('/customers/<int:id>', methods=['GET'])
@login_required
def api_get_customer(id):
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({'error': 'Not Found', 'message': 'Customer not found'}), 404

    user_id = session.get('user_id')
    user_role = session.get('user_role')
    if user_role == 'SalesExecutive' and customer.owner_id != user_id:
        return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403

    return jsonify(customer.to_dict()), 200

@api_bp.route('/customers', methods=['POST'])
@login_required
def api_create_customer():
    data = request.get_json() or {}
    customer_name = data.get('customer_name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    company_name = data.get('company_name', '').strip()
    owner_id = data.get('owner_id', session.get('user_id'))

    if not customer_name:
        return jsonify({'error': 'Validation Error', 'message': 'Customer name is required'}), 400

    valid_e, msg_e = validate_email(email)
    if not valid_e:
        return jsonify({'error': 'Validation Error', 'message': msg_e}), 400

    valid_p, msg_p = validate_phone(phone)
    if not valid_p:
        return jsonify({'error': 'Validation Error', 'message': msg_p}), 400

    if Customer.query.filter_by(email=email).first():
        return jsonify({'error': 'Conflict', 'message': 'Customer email already exists'}), 409

    if Customer.query.filter_by(phone=phone).first():
        return jsonify({'error': 'Conflict', 'message': 'Customer phone already exists'}), 409

    cust_code = f"CUST-{uuid.uuid4().hex[:6].upper()}"
    customer = Customer(
        customer_code=cust_code,
        customer_name=customer_name,
        email=email,
        phone=phone,
        company_name=company_name,
        owner_id=int(owner_id),
        created_by=session.get('user_name')
    )
    db.session.add(customer)
    db.session.commit()

    log_audit(action='API Create', entity_name='Customer', record_id=customer.id)
    return jsonify(customer.to_dict()), 201

@api_bp.route('/customers/<int:id>', methods=['PUT'])
@login_required
def api_update_customer(id):
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({'error': 'Not Found', 'message': 'Customer not found'}), 404

    data = request.get_json() or {}
    customer_name = data.get('customer_name', customer.customer_name).strip()
    email = data.get('email', customer.email).strip().lower()
    phone = data.get('phone', customer.phone).strip()

    valid_e, msg_e = validate_email(email)
    if not valid_e:
        return jsonify({'error': 'Validation Error', 'message': msg_e}), 400

    valid_p, msg_p = validate_phone(phone)
    if not valid_p:
        return jsonify({'error': 'Validation Error', 'message': msg_p}), 400

    customer.customer_name = customer_name
    customer.email = email
    customer.phone = phone
    customer.company_name = data.get('company_name', customer.company_name)
    customer.status = data.get('status', customer.status)

    db.session.commit()
    log_audit(action='API Update', entity_name='Customer', record_id=customer.id)
    return jsonify(customer.to_dict()), 200

@api_bp.route('/customers/<int:id>', methods=['DELETE'])
@login_required
@role_required('Admin', 'Manager')
def api_delete_customer(id):
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({'error': 'Not Found', 'message': 'Customer not found'}), 404

    db.session.delete(customer)
    db.session.commit()
    log_audit(action='API Delete', entity_name='Customer', record_id=id)
    return jsonify({'message': f'Customer {id} deleted successfully'}), 200

# --- LEADS REST API ---
@api_bp.route('/leads', methods=['GET'])
@login_required
def api_get_leads():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if user_role in ['Admin', 'Manager']:
        leads = Lead.query.all()
    else:
        leads = Lead.query.filter_by(owner_id=user_id).all()

    return jsonify([l.to_dict() for l in leads]), 200

@api_bp.route('/leads', methods=['POST'])
@login_required
def api_create_lead():
    data = request.get_json() or {}
    lead_name = data.get('lead_name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    source = data.get('source', 'Web')
    status = data.get('status', 'New')
    expected_value = data.get('expected_value', 0)

    valid_r, msg_r = validate_lead_rules(lead_name, status, expected_value)
    if not valid_r:
        return jsonify({'error': 'Validation Error', 'message': msg_r}), 400

    lead_code = f"LEAD-{uuid.uuid4().hex[:6].upper()}"
    lead = Lead(
        lead_code=lead_code,
        lead_name=lead_name,
        email=email,
        phone=phone,
        source=source,
        status=status,
        expected_value=float(expected_value),
        owner_id=session.get('user_id')
    )
    db.session.add(lead)
    db.session.commit()

    log_audit(action='API Create', entity_name='Lead', record_id=lead.id)
    return jsonify(lead.to_dict()), 201

# --- OPPORTUNITIES REST API ---
@api_bp.route('/opportunities', methods=['GET'])
@login_required
def api_get_opportunities():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if user_role in ['Admin', 'Manager']:
        opps = Opportunity.query.all()
    else:
        opps = Opportunity.query.filter_by(owner_id=user_id).all()

    return jsonify([o.to_dict() for o in opps]), 200

@api_bp.route('/opportunities', methods=['POST'])
@login_required
def api_create_opportunity():
    data = request.get_json() or {}
    opportunity_name = data.get('opportunity_name', '').strip()
    customer_id = data.get('customer_id')
    amount = data.get('amount')
    stage = data.get('stage', 'Qualification')
    probability = data.get('probability', 20)
    expected_close_date_str = data.get('expected_close_date')

    if not opportunity_name:
        return jsonify({'error': 'Validation Error', 'message': 'Opportunity name is required'}), 400

    valid_r, msg_r = validate_opportunity_rules(amount, probability, expected_close_date_str, is_active=(stage not in ['Lost']))
    if not valid_r:
        return jsonify({'error': 'Validation Error', 'message': msg_r}), 400

    close_date = datetime.strptime(expected_close_date_str, '%Y-%m-%d').date()

    opp = Opportunity(
        opportunity_name=opportunity_name,
        customer_id=int(customer_id) if customer_id else None,
        amount=float(amount),
        stage=stage,
        probability=int(probability),
        expected_close_date=close_date,
        owner_id=session.get('user_id')
    )
    db.session.add(opp)
    db.session.commit()

    log_audit(action='API Create', entity_name='Opportunity', record_id=opp.id)
    return jsonify(opp.to_dict()), 201

# --- FOLLOWUPS REST API ---
@api_bp.route('/followups', methods=['GET'])
@login_required
def api_get_followups():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if user_role in ['Admin', 'Manager']:
        followups = FollowUp.query.all()
    else:
        followups = FollowUp.query.filter_by(assigned_to=user_id).all()

    return jsonify([f.to_dict() for f in followups]), 200

# --- REPORTS REST API ---
@api_bp.route('/reports/pipeline', methods=['GET'])
@login_required
@role_required('Admin', 'Manager')
def api_pipeline_report():
    stages = ['Qualification', 'Proposal', 'Negotiation', 'Won', 'Lost']
    result = []
    for s in stages:
        opps = Opportunity.query.filter_by(stage=s).all()
        result.append({
            'stage': s,
            'count': len(opps),
            'total_amount': sum(o.amount for o in opps),
            'weighted_amount': sum(o.weighted_amount for o in opps)
        })
    return jsonify({'pipeline_summary': result}), 200
