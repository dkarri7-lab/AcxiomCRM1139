import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, Customer, User, Opportunity, FollowUp
from utils.auth_utils import login_required, role_required
from utils.validation_utils import validate_email, validate_phone
from utils.audit_utils import log_audit

customer_bp = Blueprint('customer', __name__, url_prefix='/customers')

@customer_bp.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()

    if user_role in ['Admin', 'Manager']:
        query = Customer.query
    else:
        query = Customer.query.filter_by(owner_id=user_id)

    if search_query:
        query = query.filter(
            (Customer.customer_name.ilike(f'%{search_query}%')) |
            (Customer.email.ilike(f'%{search_query}%')) |
            (Customer.phone.ilike(f'%{search_query}%')) |
            (Customer.company_name.ilike(f'%{search_query}%'))
        )

    if status_filter:
        query = query.filter_by(status=status_filter)

    customers = query.order_by(Customer.created_date.desc()).all()
    return render_template('customers/index.html', customers=customers, search_query=search_query, status_filter=status_filter)

@customer_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        company_name = request.form.get('company_name', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        owner_id = request.form.get('owner_id', session.get('user_id'))

        # Mandatory Validations
        if not customer_name:
            flash('Customer Name is required.', 'danger')
            return render_template('customers/create.html', sales_execs=User.query.all())

        valid_e, msg_e = validate_email(email)
        if not valid_e:
            flash(msg_e, 'danger')
            return render_template('customers/create.html', sales_execs=User.query.all())

        valid_p, msg_p = validate_phone(phone)
        if not valid_p:
            flash(msg_p, 'danger')
            return render_template('customers/create.html', sales_execs=User.query.all())

        # Uniqueness Validation
        if Customer.query.filter_by(email=email).first():
            flash('A customer with this email address already exists.', 'danger')
            return render_template('customers/create.html', sales_execs=User.query.all())

        if Customer.query.filter_by(phone=phone).first():
            flash('A customer with this phone number already exists.', 'danger')
            return render_template('customers/create.html', sales_execs=User.query.all())

        # Generate Customer Code
        customer_code = f"CUST-{uuid.uuid4().hex[:6].upper()}"

        customer = Customer(
            customer_code=customer_code,
            customer_name=customer_name,
            email=email,
            phone=phone,
            company_name=company_name,
            address=address,
            city=city,
            state=state,
            owner_id=int(owner_id),
            created_by=session.get('user_name')
        )
        db.session.add(customer)
        db.session.commit()

        log_audit(action='Create', entity_name='Customer', record_id=customer.id, new_value=f'Created Customer {customer_name} ({customer_code})')
        flash(f'Customer "{customer_name}" created successfully.', 'success')
        return redirect(url_for('customer.index'))

    sales_execs = User.query.filter_by(is_active=True).all()
    return render_template('customers/create.html', sales_execs=sales_execs)

@customer_bp.route('/<int:id>')
@login_required
def details(id):
    customer = Customer.query.get_or_404(id)
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if user_role == 'SalesExecutive' and customer.owner_id != user_id:
        flash('You are not authorized to view this customer.', 'danger')
        return redirect(url_for('customer.index'))

    opportunities = Opportunity.query.filter_by(customer_id=id).all()
    followups = FollowUp.query.filter_by(customer_id=id).order_by(FollowUp.followup_date.desc()).all()

    return render_template('customers/details.html', customer=customer, opportunities=opportunities, followups=followups)

@customer_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    customer = Customer.query.get_or_404(id)
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if user_role == 'SalesExecutive' and customer.owner_id != user_id:
        flash('You are not authorized to edit this customer.', 'danger')
        return redirect(url_for('customer.index'))

    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        company_name = request.form.get('company_name', '').strip()
        address = request.form.get('address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        status = request.form.get('status', 'Active')
        owner_id = request.form.get('owner_id', customer.owner_id)

        if not customer_name:
            flash('Customer Name is required.', 'danger')
            return render_template('customers/edit.html', customer=customer, sales_execs=User.query.all())

        valid_e, msg_e = validate_email(email)
        if not valid_e:
            flash(msg_e, 'danger')
            return render_template('customers/edit.html', customer=customer, sales_execs=User.query.all())

        valid_p, msg_p = validate_phone(phone)
        if not valid_p:
            flash(msg_p, 'danger')
            return render_template('customers/edit.html', customer=customer, sales_execs=User.query.all())

        # Uniqueness Check excluding self
        existing_e = Customer.query.filter(Customer.email == email, Customer.id != id).first()
        if existing_e:
            flash('Another customer is already registered with this email address.', 'danger')
            return render_template('customers/edit.html', customer=customer, sales_execs=User.query.all())

        existing_p = Customer.query.filter(Customer.phone == phone, Customer.id != id).first()
        if existing_p:
            flash('Another customer is already registered with this phone number.', 'danger')
            return render_template('customers/edit.html', customer=customer, sales_execs=User.query.all())

        old_val = f"Name: {customer.customer_name}, Email: {customer.email}, Status: {customer.status}"

        customer.customer_name = customer_name
        customer.email = email
        customer.phone = phone
        customer.company_name = company_name
        customer.address = address
        customer.city = city
        customer.state = state
        customer.status = status
        customer.owner_id = int(owner_id)

        db.session.commit()

        log_audit(action='Update', entity_name='Customer', record_id=customer.id, old_value=old_val, new_value=f"Name: {customer.customer_name}, Email: {customer.email}, Status: {customer.status}")
        flash(f'Customer "{customer_name}" updated successfully.', 'success')
        return redirect(url_for('customer.details', id=id))

    sales_execs = User.query.filter_by(is_active=True).all()
    return render_template('customers/edit.html', customer=customer, sales_execs=sales_execs)

@customer_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin', 'Manager')
def delete(id):
    customer = Customer.query.get_or_404(id)
    name = customer.customer_name
    db.session.delete(customer)
    db.session.commit()

    log_audit(action='Delete', entity_name='Customer', record_id=id, old_value=f'Deleted Customer {name}')
    flash(f'Customer "{name}" has been deleted.', 'info')
    return redirect(url_for('customer.index'))
