from flask import Flask
from config import UPLOAD_FOLDER
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config') 
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  

    db.init_app(app)  # Initialize the database

    # Register Blueprints (if any)
    from app.views import views
    app.register_blueprint(views)

    return app
