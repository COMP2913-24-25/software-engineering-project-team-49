from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
import threading
import time
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()

def check_auctions(app):
    """Background thread that checks for expired auctions."""
    from app.models import db, Item, Bid, Notification, ItemStatus
    while True:
        with app.app_context():  # Ensure we have access to the database
            now = datetime.utcnow()

            # Find items whose auction has ended but still marked as ACTIVE
            expired_items = Item.query.filter(Item.end_time <= now, Item.status == ItemStatus.ACTIVE.value).all()

            for item in expired_items:
                # Find the highest bid
                highest_bid = Bid.query.filter(Bid.item_id == item.id).order_by(Bid.amount.desc()).first()

                if highest_bid:
                    # Notify the winner
                    winner_notification = Notification(
                        user_id=highest_bid.user_id,
                        item_id=item.id,
                        type="won",
                        message=f"Congratulations! You have won the auction for '{item.name}' with a bid of £{highest_bid.amount:.2f}."
                    )
                    db.session.add(winner_notification)
                    item.status = ItemStatus.SOLD.value

                else:
                    # No bids, so notify the seller
                    seller_notification = Notification(
                        user_id=item.seller_id,
                        item_id=item.id,
                        type="ended",
                        message=f"Your auction for '{item.name}' has ended with no bids."
                    )
                    db.session.add(seller_notification)
                    item.status = ItemStatus.EXPIRED.value

            db.session.commit()

        time.sleep(60)  # Run every 60 seconds

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    Bootstrap(app)
    csrf = CSRFProtect(app)

    db.init_app(app)
    Migrate(app, db)

    login_manager = LoginManager(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    from app import models
    from app.views import views  # Import blueprint
    app.register_blueprint(views, url_prefix='/')

    # Start background thread
    thread = threading.Thread(target=check_auctions, args=(app,), daemon=True)
    thread.start()


    return app
