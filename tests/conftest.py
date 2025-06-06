import pytest
from app import create_app, db
from app.models import User, Item, Bid
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
from flask import url_for

@pytest.fixture
def app():
    app = create_app()
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # Use in-memory DB for tests

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Return a test client for making HTTP requests."""
    return app.test_client()

@pytest.fixture
def init_database(app):
    """Pre-populate the database with test data."""
    user1 = User(username="testuser", email="testuser@gmail.com" ,password_hash="hashedpassword")
    item1 = Item(name="Vintage Clock", description="An old clock", current_price=100, minimum_price=100, seller_id=1, end_time=datetime(2025, 3, 2, 23, 59, 59))
    db.session.add_all([user1, item1])
    db.session.commit()
    yield db  # Provide database to tests
    db.session.remove()
    db.drop_all()

@pytest.fixture
def authenticated_client(client, init_database):
    """Ensure a user is logged in before testing protected routes."""
    user = User(username="testuser2", email="test@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    client.post(url_for("views.login"), data={
        "username": "testuser2",
        "password": "password123"
    }, follow_redirects=True)

    return client

