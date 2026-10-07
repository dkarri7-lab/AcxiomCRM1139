from flask import Blueprint, render_template, session, jsonify
from models import db, Customer, Lead, Opportunity, FollowUp, User
from utils.auth_utils import login_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    # Scoped Query Filters
    if user_role == 'Admin':
        customer_query = Customer.query
        lead_query = Lead.query
        opp_query = Opportunity.query
        followup_query = FollowUp.query
    elif user_role == 'Manager':
        # Manager sees team data
        customer_query = Customer.query
        lead_query = Lead.query
        opp_query = Opportunity.query
        followup_query = FollowUp.query
    else:
        # SalesExecutive sees assigned scope only
        customer_query = Customer.query.filter_by(owner_id=user_id)
        lead_query = Lead.query.filter_by(owner_id=user_id)
        opp_query = Opportunity.query.filter_by(owner_id=user_id)
        followup_query = FollowUp.query.filter_by(assigned_to=user_id)

    total_customers = customer_query.count()
    total_leads = lead_query.count()
    open_leads = lead_query.filter(Lead.status.notin_(['Converted', 'Lost'])).count()
    
    total_opportunities = opp_query.count()
    open_opportunities_list = opp_query.filter(Opportunity.stage.in_(['Qualification', 'Proposal', 'Negotiation'])).all()
    open_opportunities_count = len(open_opportunities_list)
    won_opportunities_count = opp_query.filter_by(stage='Won').count()
    lost_opportunities_count = opp_query.filter_by(stage='Lost').count()

    total_pipeline_value = sum(o.amount for o in open_opportunities_list)
    pending_followups_count = followup_query.filter_by(status='Planned').count()

    kpis = {
        'total_customers': total_customers,
        'total_leads': total_leads,
        'open_leads': open_leads,
        'total_opportunities': total_opportunities,
        'open_opportunities': open_opportunities_count,
        'won_opportunities': won_opportunities_count,
        'lost_opportunities': lost_opportunities_count,
        'total_pipeline_value': round(total_pipeline_value, 2),
        'pending_followups': pending_followups_count
    }

    # Recent Activities & Upcoming Followups
    recent_followups = followup_query.filter_by(status='Planned').order_by(FollowUp.followup_date.asc()).limit(5).all()

    return render_template('dashboard/index.html', kpis=kpis, recent_followups=recent_followups)

@dashboard_bp.route('/api/dashboard/chart-data')
@login_required
def chart_data():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    if user_role in ['Admin', 'Manager']:
        lead_query = Lead.query
        opp_query = Opportunity.query
    else:
        lead_query = Lead.query.filter_by(owner_id=user_id)
        opp_query = Opportunity.query.filter_by(owner_id=user_id)

    # 1. Lead Status Breakdown Chart Data
    lead_statuses = ['New', 'Contacted', 'Qualified', 'Unqualified', 'Converted', 'Lost']
    lead_counts = [lead_query.filter_by(status=s).count() for s in lead_statuses]

    # 2. Opportunity Pipeline Stages Chart Data
    pipeline_stages = ['Qualification', 'Proposal', 'Negotiation', 'Won', 'Lost']
    pipeline_counts = [opp_query.filter_by(stage=s).count() for s in pipeline_stages]
    pipeline_values = [sum(o.amount for o in opp_query.filter_by(stage=s).all()) for s in pipeline_stages]

    return jsonify({
        'lead_chart': {
            'labels': lead_statuses,
            'data': lead_counts
        },
        'pipeline_chart': {
            'labels': pipeline_stages,
            'counts': pipeline_counts,
            'values': pipeline_values
        }
    })
