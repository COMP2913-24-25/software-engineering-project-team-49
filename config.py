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

    #Upload folder for images
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')

class ProductionConfig(Config):
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')

config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}