import unittest
from datetime import datetime, timedelta, date
from app import create_app
from models import db, User, Customer, Lead, Opportunity, FollowUp, AuditLog
from utils.auth_utils import validate_password_policy
from utils.validation_utils import validate_opportunity_rules, validate_followup_rules, validate_email, validate_phone

class AcxiomCRMTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def test_password_policy(self):
        # Invalid passwords
        valid, msg = validate_password_policy('short')
        self.assertFalse(valid)

        valid, msg = validate_password_policy('nouppercase1!')
        self.assertFalse(valid)

        # Valid password
        valid, msg = validate_password_policy('ValidPass123!')
        self.assertTrue(valid)

    def test_business_validations(self):
        # Opportunity Amount <= 0 rejected
        valid, msg = validate_opportunity_rules(amount=0, probability=50, expected_close_date_str='2030-01-01')
        self.assertFalse(valid)
        self.assertIn('greater than 0', msg)

        # Probability > 100 rejected
        valid, msg = validate_opportunity_rules(amount=1000, probability=150, expected_close_date_str='2030-01-01')
        self.assertFalse(valid)
        self.assertIn('between 0 and 100', msg)

        # Past close date rejected
        past_date = (date.today() - timedelta(days=5)).strftime('%Y-%m-%d')
        valid, msg = validate_opportunity_rules(amount=1000, probability=50, expected_close_date_str=past_date)
        self.assertFalse(valid)
        self.assertIn('cannot be in the past', msg)

        # Follow-Up date earlier than today rejected
        valid, msg = validate_followup_rules(followup_date_str=past_date, status='Planned')
        self.assertFalse(valid)
        self.assertIn('earlier than today', msg)

    def test_api_unauthorized_access(self):
        # Protected API requires login
        res = self.client.get('/api/customers')
        self.assertEqual(res.status_code, 401)

if __name__ == '__main__':
    unittest.main()
