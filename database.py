from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash
from models import db, Role, User, Customer, Lead, Opportunity, FollowUp, AuditLog

def init_db(app):
    with app.app_context():
        db.create_all()

        # 1. Seed Roles
        admin_role = Role.query.filter_by(role_name='Admin').first()
        if not admin_role:
            admin_role = Role(role_name='Admin', description='Full system administration & auditing access')
            db.session.add(admin_role)

        manager_role = Role.query.filter_by(role_name='Manager').first()
        if not manager_role:
            manager_role = Role(role_name='Manager', description='Team management & pipeline reports access')
            db.session.add(manager_role)

        sales_role = Role.query.filter_by(role_name='SalesExecutive').first()
        if not sales_role:
            sales_role = Role(role_name='SalesExecutive', description='Assigned customer, lead & sales execution access')
            db.session.add(sales_role)

        db.session.commit()

        # 2. Seed Default Demo Users
        admin_user = User.query.filter_by(email='admin@acxiom.com').first()
        if not admin_user:
            admin_user = User(
                name='Admin User',
                email='admin@acxiom.com',
                password_hash=generate_password_hash('Admin123!'),
                role_id=admin_role.id,
                is_active=True
            )
            db.session.add(admin_user)

        manager_user = User.query.filter_by(email='manager@acxiom.com').first()
        if not manager_user:
            manager_user = User(
                name='Sales Manager',
                email='manager@acxiom.com',
                password_hash=generate_password_hash('Manager123!'),
                role_id=manager_role.id,
                is_active=True
            )
            db.session.add(manager_user)

        sales_user = User.query.filter_by(email='sales@acxiom.com').first()
        if not sales_user:
            sales_user = User(
                name='Sales Executive',
                email='sales@acxiom.com',
                password_hash=generate_password_hash('Sales123!'),
                role_id=sales_role.id,
                is_active=True
            )
            db.session.add(sales_user)

        db.session.commit()

        # 3. Seed Sample CRM Records if empty
        if Customer.query.count() == 0:
            c1 = Customer(
                customer_code='CUST-1001',
                customer_name='Acme Corporation',
                email='contact@acme.com',
                phone='9876543210',
                company_name='Acme Group',
                city='Mumbai',
                state='Maharashtra',
                owner_id=sales_user.id,
                created_by='Admin'
            )
            c2 = Customer(
                customer_code='CUST-1002',
                customer_name='Global Tech Solutions',
                email='info@globaltech.com',
                phone='9876543211',
                company_name='Global Tech',
                city='Bengaluru',
                state='Karnataka',
                owner_id=sales_user.id,
                created_by='Admin'
            )
            db.session.add_all([c1, c2])
            db.session.commit()

            # Sample Leads
            l1 = Lead(
                lead_code='LEAD-2001',
                lead_name='Starlight Logistics',
                email='sales@starlight.com',
                phone='9876543212',
                company_name='Starlight Pvt Ltd',
                source='Web',
                status='New',
                expected_value=12000.0,
                owner_id=sales_user.id
            )
            l2 = Lead(
                lead_code='LEAD-2002',
                lead_name='Nexus HealthCare',
                email='info@nexushealth.com',
                phone='9876543213',
                company_name='Nexus Care',
                source='Referral',
                status='Qualified',
                expected_value=25000.0,
                owner_id=sales_user.id
            )
            db.session.add_all([l1, l2])
            db.session.commit()

            # Sample Opportunities
            o1 = Opportunity(
                opportunity_name='Acme Cloud Infrastructure Deal',
                customer_id=c1.id,
                amount=45000.0,
                stage='Proposal',
                probability=60,
                expected_close_date=date.today() + timedelta(days=15),
                owner_id=sales_user.id
            )
            o2 = Opportunity(
                opportunity_name='Global Tech Software Licensing',
                customer_id=c2.id,
                amount=18000.0,
                stage='Qualification',
                probability=30,
                expected_close_date=date.today() + timedelta(days=30),
                owner_id=sales_user.id
            )
            db.session.add_all([o1, o2])

            # Sample FollowUp
            f1 = FollowUp(
                subject='Quarterly Account Review & Demo',
                followup_date=datetime.utcnow() + timedelta(days=2),
                followup_type='Meeting',
                customer_id=c1.id,
                assigned_to=sales_user.id,
                status='Planned'
            )
            db.session.add(f1)
            db.session.commit()

            print("Database initialized & seeded with demo CRM data successfully.")
