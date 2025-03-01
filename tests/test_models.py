from app.models import User, Item, Bid
from datetime import datetime

def test_create_user(init_database):
    new_user = User(username="john_doe", email="johndoe@gmail.com", password_hash="securepassword")
    init_database.session.add(new_user)
    init_database.session.commit()
    
    assert new_user.id is not None
    assert new_user.username == "john_doe"

def test_create_item(init_database):
    new_item = Item(name="Painting", description="Beautiful art", current_price=200, minimum_price=200, seller_id=1, end_time=datetime(2025, 3, 2, 23, 59, 59))
    init_database.session.add(new_item)
    init_database.session.commit()

    assert new_item.id is not None
    assert new_item.name == "Painting"

def test_create_bid(init_database):
    test_user = User.query.first()
    test_item = Item.query.first()

    new_bid = Bid(amount=150, user_id=test_user.id, item_id=test_item.id)
    init_database.session.add(new_bid)
    init_database.session.commit()

    assert new_bid.id is not None
    assert new_bid.amount == 150
    assert new_bid.user_id == test_user.id
    assert new_bid.item_id == test_item.id