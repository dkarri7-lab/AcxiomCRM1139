import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'acxiom_crm_super_secret_key_2026_x89f'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'acxiom_crm.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Password & Security Lockout Policy
    MIN_PASSWORD_LENGTH = 8
    MAX_FAILED_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
