import pytest
from app import db
from flask import url_for
from app.models import User, Item, ItemStatus, Notification, Bid, Category
from datetime import datetime, timedelta

def test_welcome_page(client):
    """ Test welcome page loads correctly """
    response = client.get(url_for("views.welcome"))
    assert response.status_code == 200
    assert b"E-Commerce Website" in response.data

def test_signup(client):
    """ Test user registration """
    response = client.post(url_for("views.signup"), data={
        "username": "newuser",
        "email": "new@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "securepassword",
        "confirm_password": "securepassword"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Account successfully created" in response.data  # Flash message check
    user = User.query.filter_by(username="newuser").first()
    assert user is not None

def test_login_logout(client, init_database):
    """ Test login and logout functionality """
    user = User(username="loginuser", email="login@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    # Login test
    response = client.post(url_for("views.login"), data={
        "username": "loginuser",
        "password": "password123"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Successfully Logged In" in response.data  # Flash message check

    # Logout test
    response = client.get(url_for("views.logout"), follow_redirects=True)
    assert response.status_code == 200

def test_list_item(authenticated_client, init_database):
    """ Test listing an auction item """
    category = Category(name="Art", description="Artwork and paintings")
    init_database.session.add(category)
    db.session.commit()

    response = authenticated_client.post(url_for("views.list_item"), data={
        "name": "Antique Vase",
        "description": "A rare antique vase",
        "category": category.id,
        "minimum_price": 100,
        "duration": "3",
        "authentication": '2'  # No authentication request
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Item listed successfully" in response.data
    item = Item.query.filter_by(name="Antique Vase").first()
    assert item is not None
    assert item.status == ItemStatus.ACTIVE.value

def test_auction_list(client, init_database):
    """Ensure only active auctions are displayed."""
    seller = User(username="seller_user", email="seller@example.com")
    seller.set_password("password")
    db.session.add(seller)
    db.session.commit()

    category = Category(name="other", description="other")
    db.session.add(category)
    db.session.commit()

    item1 = Item(
        name="Active Item",
        description="A beautiful antique painting",
        category_id=category.id,
        minimum_price=100.0,
        current_price=100.0,
        seller_id=seller.id,
        status=ItemStatus.ACTIVE.value,
        end_time=datetime.utcnow() + timedelta(days=5)
    )
    item2 = Item(
        name="Pending Item",
        description="A beautiful antique painting",
        category_id=category.id,
        minimum_price=100.0,
        current_price=100.0,
        seller_id=seller.id,
        status=ItemStatus.PENDING.value,
        end_time=datetime.utcnow() + timedelta(days=5)
    )
    db.session.add(item1)
    db.session.add(item2)
    db.session.commit()

    response = client.get(url_for("views.auction_list"))
    assert response.status_code == 200
    assert b"Active Item" in response.data
    assert b"Pending Item" not in response.data

def test_search(client, init_database):
    """ Test searching for an auction item """
    seller = User(username="seller_user", email="seller@example.com")
    seller.set_password("password")
    db.session.add(seller)
    db.session.commit()

    category = Category(name="other", description="other")
    db.session.add(category)
    db.session.commit()

    item = Item(name="Golden Watch",
        description="A beautiful antique painting",
        category_id=category.id,
        minimum_price=100.0,
        current_price=100.0,
        seller_id=seller.id,
        status=ItemStatus.ACTIVE.value,
        end_time=datetime.utcnow() + timedelta(days=5)
    )
    db.session.add(item)
    db.session.commit()

    response = client.get(url_for("views.search"), query_string={"query": "Golden"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Golden Watch" in response.data

def test_place_bid(authenticated_client, init_database):
    """ Test placing a bid on an auction """
    seller = User(username="seller_user", email="seller@example.com")
    seller.set_password("password")
    db.session.add(seller)
    db.session.commit()

    category = Category(name="other", description="other")
    db.session.add(category)
    db.session.commit()

    item = Item(name="Golden Watch",
        description="A beautiful antique painting",
        category_id=category.id,
        minimum_price=100.0,
        current_price=100.0,
        seller_id=seller.id,
        status=ItemStatus.PENDING.value,
        end_time=datetime.utcnow() + timedelta(days=5)
    )
    db.session.add(item)
    db.session.commit()

    response = authenticated_client.post(url_for("views.auction_detail", item_id=item.id), data={
        "bid_amount": 120
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Bid placed successfully" in response.data
    item = Item.query.get(item.id)
    assert item.current_price == 120  # Ensure bid updated price

def test_notifications(authenticated_client, init_database):
    """ Test viewing user notifications """
    user = User.query.filter_by(username="testuser2").first()
    notification = Notification(user_id=user.id, type="bid", message="You have been outbid")
    db.session.add(notification)
    db.session.commit()

    response = authenticated_client.get(url_for("views.notifications"))
    assert response.status_code == 200
    assert b"You have been outbid" in response.data

def test_expert_dashboard(authenticated_client, init_database):
    """ Test expert availability page """
    response = authenticated_client.get(url_for("views.expert"))
    assert response.status_code == 200
    assert b"Set your availability" in response.data  # Assuming availability form contains "Set Availability"
