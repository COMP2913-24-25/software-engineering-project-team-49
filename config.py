import os

class Config:
    WTF_CSRF_ENABLED = True
    SECRET_KEY = 'a-very-secret-elephant'

    #if deployed keep session_cookie_secure as True
    SESSION_COOKIE_SECURE = True

class DevelopmentConfig(Config):
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    #SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = True

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')  # Use PostgreSQL in production
    SQLALCHEMY_TRACK_MODIFICATIONS = False

config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}