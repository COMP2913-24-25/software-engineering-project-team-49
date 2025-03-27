import os

class Config:
    WTF_CSRF_ENABLED = True
    SECRET_KEY = 'a-very-secret-elephant'

    # MailerSend SMTP Configuration
    MAIL_SERVER = 'smtp.mailersend.net'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'MS_GzN1QW@trial-r9084zvrowvgw63d.mlsender.net'
    MAIL_PASSWORD = 'mssp.eYedm8A.0r83ql3j97xgzw1j.1AGsnYx'
    MAIL_DEFAULT_SENDER = 'MS_GzN1QW@trial-r9084zvrowvgw63d.mlsender.net'
    
    #if deployed keep session_cookie_secure as True
    SESSION_COOKIE_SECURE = True

class DevelopmentConfig(Config):
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    #SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = True

class ProductionConfig(Config):
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}