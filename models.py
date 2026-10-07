from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f"<Role {self.role_name}>"

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    failed_login_count = db.Column(db.Integer, default=0, nullable=False)
    lockout_until = db.Column(db.DateTime, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    customers = db.relationship('Customer', backref='owner', foreign_keys='Customer.owner_id', lazy=True)
    leads = db.relationship('Lead', backref='owner', foreign_keys='Lead.owner_id', lazy=True)
    opportunities = db.relationship('Opportunity', backref='owner', foreign_keys='Opportunity.owner_id', lazy=True)
    followups = db.relationship('FollowUp', backref='assigned_user', foreign_keys='FollowUp.assigned_to', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role.role_name if self.role else None,
            'is_active': self.is_active,
            'failed_login_count': self.failed_login_count,
            'lockout_until': self.lockout_until.isoformat() if self.lockout_until else None,
            'created_date': self.created_date.isoformat()
        }

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(30), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    company_name = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='Active', nullable=False) # Active, Inactive
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(100), nullable=True)

    opportunities = db.relationship('Opportunity', backref='customer', lazy=True)
    followups = db.relationship('FollowUp', backref='customer', lazy=True)
    activities = db.relationship('Activity', backref='customer', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_code': self.customer_code,
            'customer_name': self.customer_name,
            'email': self.email,
            'phone': self.phone,
            'company_name': self.company_name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'status': self.status,
            'owner_id': self.owner_id,
            'owner_name': self.owner.name if self.owner else None,
            'created_date': self.created_date.isoformat()
        }

class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    lead_code = db.Column(db.String(30), unique=True, nullable=False)
    lead_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    company_name = db.Column(db.String(100), nullable=True)
    source = db.Column(db.String(50), nullable=False) # Web, Referral, Cold Call, Campaign
    status = db.Column(db.String(30), default='New', nullable=False) # New, Contacted, Qualified, Unqualified, Converted, Lost
    priority = db.Column(db.String(20), default='Medium', nullable=False) # Low, Medium, High
    expected_value = db.Column(db.Float, default=0.0, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    opportunities = db.relationship('Opportunity', backref='lead', lazy=True)
    followups = db.relationship('FollowUp', backref='lead', lazy=True)
    activities = db.relationship('Activity', backref='lead', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'lead_code': self.lead_code,
            'lead_name': self.lead_name,
            'email': self.email,
            'phone': self.phone,
            'company_name': self.company_name,
            'source': self.source,
            'status': self.status,
            'priority': self.priority,
            'expected_value': self.expected_value,
            'owner_id': self.owner_id,
            'owner_name': self.owner.name if self.owner else None,
            'created_date': self.created_date.isoformat()
        }

class Opportunity(db.Model):
    __tablename__ = 'opportunities'
    id = db.Column(db.Integer, primary_key=True)
    opportunity_name = db.Column(db.String(100), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    stage = db.Column(db.String(30), nullable=False) # Qualification, Proposal, Negotiation, Won, Lost
    probability = db.Column(db.Integer, nullable=False) # 0 to 100
    expected_close_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='Active', nullable=False) # Active, Won, Lost
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def weighted_amount(self):
        return (self.amount * self.probability) / 100.0

    def to_dict(self):
        return {
            'id': self.id,
            'opportunity_name': self.opportunity_name,
            'customer_id': self.customer_id,
            'customer_name': self.customer.customer_name if self.customer else None,
            'lead_id': self.lead_id,
            'amount': self.amount,
            'stage': self.stage,
            'probability': self.probability,
            'weighted_amount': self.weighted_amount,
            'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None,
            'status': self.status,
            'owner_id': self.owner_id,
            'owner_name': self.owner.name if self.owner else None,
            'created_date': self.created_date.isoformat()
        }

class FollowUp(db.Model):
    __tablename__ = 'followups'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=True)
    followup_date = db.Column(db.DateTime, nullable=False)
    followup_type = db.Column(db.String(30), nullable=False) # Call, Meeting, Email, Task
    subject = db.Column(db.String(150), nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Planned', nullable=False) # Planned, Completed, Missed, Cancelled
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.customer_name if self.customer else None,
            'lead_id': self.lead_id,
            'lead_name': self.lead.lead_name if self.lead else None,
            'followup_date': self.followup_date.strftime('%Y-%m-%d %H:%M'),
            'followup_type': self.followup_type,
            'subject': self.subject,
            'remarks': self.remarks,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'assigned_to_name': self.assigned_user.name if self.assigned_user else None,
            'created_date': self.created_date.isoformat()
        }

class Activity(db.Model):
    __tablename__ = 'activities'
    id = db.Column(db.Integer, primary_key=True)
    activity_type = db.Column(db.String(30), nullable=False) # Call, Meeting, Email, Task
    subject = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    activity_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='Completed', nullable=False)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False) # Login, Login Failure, Create, Update, Delete, Role Change, Security
    entity_name = db.Column(db.String(50), nullable=True) # User, Customer, Lead, Opportunity, FollowUp
    record_id = db.Column(db.String(50), nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else 'System / Anonymous',
            'action': self.action,
            'entity_name': self.entity_name,
            'record_id': self.record_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'created_date': self.created_date.strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': self.ip_address
        }
