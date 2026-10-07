from flask import Blueprint, render_template, request, session, jsonify
from models import db, Customer, Lead, Opportunity, FollowUp, User, AuditLog
from utils.auth_utils import login_required

report_bp = Blueprint('report', __name__, url_prefix='/reports')

@report_bp.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    user_role = session.get('user_role')

    # Scoped Query Filters
    if user_role in ['Admin', 'Manager']:
        customer_query = Customer.query
        lead_query = Lead.query
        opp_query = Opportunity.query
        followup_query = FollowUp.query
    else:
        customer_query = Customer.query.filter_by(owner_id=user_id)
        lead_query = Lead.query.filter_by(owner_id=user_id)
        opp_query = Opportunity.query.filter_by(owner_id=user_id)
        followup_query = FollowUp.query.filter_by(assigned_to=user_id)

    # 1. Pipeline Summary by Stage
    stages = ['Qualification', 'Proposal', 'Negotiation', 'Won', 'Lost']
    pipeline_report = []
    for s in stages:
        opps = opp_query.filter_by(stage=s).all()
        count = len(opps)
        total_val = sum(o.amount for o in opps)
        weighted_val = sum(o.weighted_amount for o in opps)
        pipeline_report.append({
            'stage': s,
            'count': count,
            'total_value': round(total_val, 2),
            'weighted_value': round(weighted_val, 2)
        })

    # 2. Lead Conversion Metrics
    total_leads = lead_query.count()
    converted_leads = lead_query.filter_by(status='Converted').count()
    lost_leads = lead_query.filter_by(status='Lost').count()
    conversion_rate = round((converted_leads / total_leads * 100), 1) if total_leads > 0 else 0

    # 3. Follow-Up Metrics
    planned_f = followup_query.filter_by(status='Planned').count()
    completed_f = followup_query.filter_by(status='Completed').count()
    missed_f = followup_query.filter_by(status='Missed').count()

    metrics = {
        'total_leads': total_leads,
        'converted_leads': converted_leads,
        'lost_leads': lost_leads,
        'conversion_rate': conversion_rate,
        'planned_followups': planned_f,
        'completed_followups': completed_f,
        'missed_followups': missed_f
    }

    return render_template('reports/index.html', pipeline_report=pipeline_report, metrics=metrics)
