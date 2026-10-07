from flask import Flask
from config import Config
from models import db
from database import init_db

# Import Blueprints
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.customer_routes import customer_bp
from routes.lead_routes import lead_bp
from routes.opportunity_routes import opportunity_bp
from routes.followup_routes import followup_bp
from routes.user_routes import user_bp
from routes.audit_routes import audit_bp
from routes.report_routes import report_bp
from routes.api_routes import api_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(lead_bp)
    app.register_blueprint(opportunity_bp)
    app.register_blueprint(followup_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(api_bp)

    # Init & Seed Database
    init_db(app)

    return app

app = create_app()

if __name__ == '__main__':
    print("==================================================")
    print(" AcxiomCRM Enterprise Application Starting...")
    print(" URL: http://127.0.0.1:5000")
    print(" Default Login Credentials:")
    print("   Admin:     admin@acxiom.com / Admin123!")
    print("   Manager:   manager@acxiom.com / Manager123!")
    print("   SalesExec: sales@acxiom.com / Sales123!")
    print("==================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)
