import pytest
from app.models import (
    User, Item, Bid, Category, ItemImage, AuthenticationRequest, 
    AuthenticationMessage, Payment, Notification, SystemConfiguration,
    ExpertCategory, ExpertAvailability, UserPriority, ItemStatus, 
    AuthenticationStatus
)
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash

# =====================
# User Model Tests
# =====================

def test_user_creation(init_database):
    """Test basic user creation with required fields."""
    user = User(
        username="newuser", 
        email="new@example.com", 
        first_name="John", 
        last_name="Doe"
    )
    user.set_password("password123")
    init_database.session.add(user)
    init_database.session.commit()
    
    saved_user = User.query.filter_by(username="newuser").first()
    assert saved_user is not None
    assert saved_user.email == "new@example.com"
    assert saved_user.first_name == "John"
    assert saved_user.last_name == "Doe"
    assert saved_user.priority == UserPriority.GENERAL_USER.value

def test_user_unique_constraints(init_database):
    """Test that username and email must be unique."""
    user1 = User(username="unique_user", email="unique@example.com")
    user1.set_password("password123")
    init_database.session.add(user1)
    init_database.session.commit()
    
    # Create another user with the same username
    user2 = User(username="unique_user", email="different@example.com")
    user2.set_password("password123")
    init_database.session.add(user2)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()
    
    init_database.session.rollback()
    
    # Create another user with the same email
    user3 = User(username="different_user", email="unique@example.com")
    user3.set_password("password123")
    init_database.session.add(user3)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()

def test_password_hashing(init_database):
    """Test that passwords are properly hashed and can be verified."""
    user = User(username="password_user", email="password@example.com")
    plain_password = "secure_password"
    user.set_password(plain_password)
    init_database.session.add(user)
    init_database.session.commit()
    
    saved_user = User.query.filter_by(username="password_user").first()
    assert saved_user.password_hash != plain_password
    assert saved_user.check_password(plain_password) is True
    assert saved_user.check_password("wrong_password") is False

def test_user_roles(init_database):
    """Test user priority levels and role checking methods."""
    general_user = User(
        username="general", 
        email="general@example.com", 
        priority=UserPriority.GENERAL_USER.value
    )
    general_user.set_password("password")
    expert_user = User(
        username="expert", 
        email="expert@example.com", 
        priority=UserPriority.EXPERT.value
    )
    expert_user.set_password("password")
    manager_user = User(
        username="manager", 
        email="manager@example.com", 
        priority=UserPriority.MANAGER.value
    )
    manager_user.set_password("password")
    
    init_database.session.add_all([general_user, expert_user, manager_user])
    init_database.session.commit()
    
    # Test is_expert() method
    assert general_user.is_expert() is False
    assert expert_user.is_expert() is True
    assert manager_user.is_expert() is True
    
    # Test is_manager() method
    assert general_user.is_manager() is False
    assert expert_user.is_manager() is False
    assert manager_user.is_manager() is True

def test_card_details_storage(init_database):
    """Test storing and retrieving card details."""
    user = User(
        username="card_user", 
        email="card@example.com",
        card_number_hash="hashed_card_number",
        card_expiry="12/25"
    )
    user.set_password("password")
    init_database.session.add(user)
    init_database.session.commit()
    
    saved_user = User.query.filter_by(username="card_user").first()
    assert saved_user.card_number_hash == "hashed_card_number"
    assert saved_user.card_expiry == "12/25"

def test_required_fields_validation(init_database):
    """Test validation of required fields for User model."""
    # Test missing username
    user1 = User(email="missing_username@example.com")
    user1.set_password("password")
    init_database.session.add(user1)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()
    
    init_database.session.rollback()
    
    # Test missing email
    user2 = User(username="missing_email")
    user2.set_password("password")
    init_database.session.add(user2)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()
    
    init_database.session.rollback()

def test_default_priority_setting(init_database):
    """Test that default priority is set to GENERAL_USER."""
    user = User(username="default_priority", email="default@example.com")
    user.set_password("password")
    init_database.session.add(user)
    init_database.session.commit()
    
    saved_user = User.query.filter_by(username="default_priority").first()
    assert saved_user.priority == UserPriority.GENERAL_USER.value

def test_user_relationships_comprehensive(init_database):
    """Test all user relationships comprehensively."""
    # Create users
    seller = User(username="rel_seller_comp", email="rel_seller_comp@example.com")
    buyer = User(username="rel_buyer_comp", email="rel_buyer_comp@example.com")
    expert = User(
        username="rel_expert_comp", 
        email="rel_expert_comp@example.com",
        priority=UserPriority.EXPERT.value
    )
    
    seller.set_password("password")
    buyer.set_password("password")
    expert.set_password("password")
    
    init_database.session.add_all([seller, buyer, expert])
    init_database.session.flush()
    
    # Create a category
    category = Category(name="Fine Art", description="Fine art pieces")
    init_database.session.add(category)
    init_database.session.flush()
    
    # Create items (some sold, some active)
    sold_item = Item(
        name="Sold Painting",
        description="A sold painting",
        category_id=category.id,
        minimum_price=100.0,
        current_price=150.0,
        seller_id=seller.id,
        winner_id=buyer.id,
        status=ItemStatus.SOLD.value,
        end_time=datetime.utcnow() - timedelta(days=1)
    )
    
    active_item = Item(
        name="Active Sculpture",
        description="An active auction",
        category_id=category.id,
        minimum_price=200.0,
        current_price=200.0,
        seller_id=seller.id,
        status=ItemStatus.ACTIVE.value,
        end_time=datetime.utcnow() + timedelta(days=3)
    )
    
    init_database.session.add_all([sold_item, active_item])
    init_database.session.flush()
    
    # Create bids
    bid1 = Bid(item_id=active_item.id, user_id=buyer.id, amount=210.0)
    bid2 = Bid(item_id=active_item.id, user_id=buyer.id, amount=220.0)
    
    init_database.session.add_all([bid1, bid2])
    init_database.session.flush()
    
    # Add expertise for expert
    expertise = ExpertCategory(
        user_id=expert.id,
        category="Fine Art",
        expertise_description="Contemporary art expert"
    )
    
    # Add availability for expert
    now = datetime.utcnow()
    availability = ExpertAvailability(
        user_id=expert.id,
        day_of_week = "Monday",
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=4)
    )
    
    init_database.session.add_all([expertise, availability])
    
    # Add watching relationships
    buyer.watched_items.append(active_item)
    expert.watched_items.append(active_item)
    
    init_database.session.commit()
    
    # Test seller's relationships
    assert len(seller.items_sold.all()) == 2
    assert sold_item in seller.items_sold.all()
    assert active_item in seller.items_sold.all()
    
    # Test buyer's relationships
    assert len(buyer.items_won.all()) == 1
    assert sold_item in buyer.items_won.all()
    assert len(buyer.bids.all()) == 2
    assert len(buyer.watched_items.all()) == 1
    assert active_item in buyer.watched_items.all()
    
    # Test expert's relationships
    assert len(expert.expertise.all()) == 1
    assert expert.expertise.first().category == "Fine Art"
    assert len(expert.availability.all()) == 1
    assert len(expert.watched_items.all()) == 1

def test_raw_password_not_stored(init_database):
    """Test that raw passwords are never stored in the database."""
    user = User(username="secure_user", email="secure@example.com")
    plain_password = "very_secure_password"
    user.set_password(plain_password)
    init_database.session.add(user)
    init_database.session.commit()
    
    saved_user = User.query.filter_by(username="secure_user").first()
    # Make sure there's no attribute storing the plain password
    assert not hasattr(saved_user, "password")
    # Make sure the hash doesn't contain the raw password
    assert plain_password not in saved_user.password_hash

# =====================
# Item Model Tests
# =====================

def test_item_creation(init_database):
    """Test creating an item with required fields."""
    # Create a seller user
    seller = User(username="seller", email="seller@example.com")
    seller.set_password("password")
    init_database.session.add(seller)
    init_database.session.flush()
    
    # Create a category
    category = Category(name="Art", description="Artwork and paintings")
    init_database.session.add(category)
    init_database.session.flush()
    
    # Create an item
    item = Item(
        name="Antique Painting",
        description="A beautiful antique painting",
        category_id=category.id,
        minimum_price=100.0,
        current_price=100.0,
        seller_id=seller.id,
        status=ItemStatus.PENDING.value,
        end_time=datetime.utcnow() + timedelta(days=5)
    )
    init_database.session.add(item)
    init_database.session.commit()
    
    saved_item = Item.query.filter_by(name="Antique Painting").first()
    assert saved_item is not None
    assert saved_item.description == "A beautiful antique painting"
    assert saved_item.minimum_price == 100.0
    assert saved_item.current_price == 100.0
    assert saved_item.seller_id == seller.id
    assert saved_item.category_id == category.id
    assert saved_item.status == ItemStatus.PENDING.value
    assert saved_item.is_authenticated is False

def test_item_status_methods(init_database):
    """Test item status and timeline methods."""
    # Create a seller
    seller = User(username="status_seller", email="status_seller@example.com")
    seller.set_password("password")
    init_database.session.add(seller)
    init_database.session.flush()
    
    now = datetime.utcnow()
    
    # Create items with different statuses and times
    active_item = Item(
        name="Active Item",
        minimum_price=50.0,
        current_price=50.0,
        seller_id=seller.id,
        status=ItemStatus.ACTIVE.value,
        start_time=now - timedelta(days=1),
        end_time=now + timedelta(days=1)
    )
    
    expired_item = Item(
        name="Expired Item",
        minimum_price=50.0,
        current_price=50.0,
        seller_id=seller.id,
        status=ItemStatus.ACTIVE.value,
        start_time=now - timedelta(days=2),
        end_time=now - timedelta(days=1)
    )
    
    pending_item = Item(
        name="Pending Item",
        minimum_price=50.0,
        current_price=50.0,
        seller_id=seller.id,
        status=ItemStatus.PENDING.value,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=2)
    )
    
    init_database.session.add_all([active_item, expired_item, pending_item])
    init_database.session.commit()
    
    # Test is_active() method
    assert active_item.is_active() is True
    assert expired_item.is_active() is False
    assert pending_item.is_active() is False
    
    # Test time_left() method
    assert active_item.time_left() > 0
    assert expired_item.time_left() == 0
    assert pending_item.time_left() > 0

def test_item_relationships(init_database):
    """Test relationships between Item and other models."""
    # Create users
    seller = User(username="rel_seller", email="rel_seller@example.com")
    buyer = User(username="rel_buyer", email="rel_buyer@example.com")
    seller.set_password("password")
    buyer.set_password("password")
    init_database.session.add_all([seller, buyer])
    init_database.session.flush()
    
    # Create a category
    category = Category(name="Electronics", description="Electronic devices")
    init_database.session.add(category)
    init_database.session.flush()
    
    # Create an item
    item = Item(
        name="Vintage Radio",
        description="A vintage radio from the 1950s",
        category_id=category.id,
        minimum_price=75.0,
        current_price=75.0,
        seller_id=seller.id,
        end_time=datetime.utcnow() + timedelta(days=3)
    )
    init_database.session.add(item)
    init_database.session.flush()
    
    # Add some bids
    bid1 = Bid(item_id=item.id, user_id=buyer.id, amount=80.0)
    bid2 = Bid(item_id=item.id, user_id=buyer.id, amount=85.0)
    init_database.session.add_all([bid1, bid2])
    
    # Add an image
    image = ItemImage(item_id=item.id, image_path="/path/to/image.jpg")
    init_database.session.add(image)
    
    # Add to watched items
    buyer.watched_items.append(item)
    
    init_database.session.commit()
    
    # Test relationships
    saved_item = Item.query.get(item.id)
    assert saved_item.seller.username == "rel_seller"
    assert saved_item.category_rel.name == "Electronics"
    assert len(saved_item.bids.all()) == 2
    assert saved_item.bids.order_by(Bid.amount.desc()).first().amount == 85.0
    assert len(saved_item.images.all()) == 1
    assert saved_item.images.first().image_path == "/path/to/image.jpg"
    assert saved_item in buyer.watched_items.all()
    assert buyer in saved_item.watchers.all()

def test_item_required_fields_validation(init_database):
    """Test validation of required fields for Item model."""
    # Create a seller
    seller = User(username="req_seller", email="req_seller@example.com")
    seller.set_password("password")
    init_database.session.add(seller)
    init_database.session.flush()
    
    # Test missing name
    item1 = Item(
        minimum_price=50.0,
        current_price=50.0,
        seller_id=seller.id,
        end_time=datetime.utcnow() + timedelta(days=1)
    )
    init_database.session.add(item1)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()
    
    init_database.session.rollback()
    
    # Test missing price
    item2 = Item(
        name="No Price Item",
        seller_id=seller.id,
        end_time=datetime.utcnow() + timedelta(days=1)
    )
    init_database.session.add(item2)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()
    
    init_database.session.rollback()
    
    # Test missing seller
    item3 = Item(
        name="No Seller Item",
        minimum_price=50.0,
        current_price=50.0,
        end_time=datetime.utcnow() + timedelta(days=1)
    )
    init_database.session.add(item3)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()

def test_item_state_transitions(init_database):
    """Test state transitions for items (pending → active → sold/expired)."""
    # Create a seller and buyer
    seller = User(username="transition_seller", email="transition_seller@example.com")
    buyer = User(username="transition_buyer", email="transition_buyer@example.com")
    seller.set_password("password")
    buyer.set_password("password")
    
    init_database.session.add_all([seller, buyer])
    init_database.session.flush()
    
    # Create a pending item
    now = datetime.utcnow()
    item = Item(
        name="Transition Test Item",
        minimum_price=100.0,
        current_price=100.0,
        seller_id=seller.id,
        status=ItemStatus.PENDING.value,
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(days=1)
    )
    
    init_database.session.add(item)
    init_database.session.commit()
    
    # Transition to active
    item.status = ItemStatus.ACTIVE.value
    item.start_time = now - timedelta(hours=1)
    init_database.session.commit()
    
    assert item.status == ItemStatus.ACTIVE.value
    assert item.is_active() is True
    
    # Add a bid
    bid = Bid(item_id=item.id, user_id=buyer.id, amount=150.0)
    init_database.session.add(bid)
    item.current_price = 150.0
    init_database.session.commit()
    
    # Transition to sold
    item.status = ItemStatus.SOLD.value
    item.winner_id = buyer.id
    item.end_time = now - timedelta(minutes=10)
    init_database.session.commit()
    
    assert item.status == ItemStatus.SOLD.value
    assert item.winner_id == buyer.id
    assert item.is_active() is False
    
    # Create another item for expired transition test
    item2 = Item(
        name="Expiring Item",
        minimum_price=200.0,
        current_price=200.0,
        seller_id=seller.id,
        status=ItemStatus.ACTIVE.value,
        start_time=now - timedelta(days=2),
        end_time=now - timedelta(hours=1)
    )
    
    init_database.session.add(item2)
    init_database.session.commit()
    
    # Transition to expired
    item2.status = ItemStatus.EXPIRED.value
    init_database.session.commit()
    
    assert item2.status == ItemStatus.EXPIRED.value
    assert item2.is_active() is False
    assert item2.time_left() == 0

def test_bid_required_fields_validation(init_database):
    """Test validation of required fields for Bid model."""
    # Create users and item
    seller = User(username="req_bid_seller", email="req_bid_seller@example.com")
    bidder = User(username="req_bidder", email="req_bidder@example.com")
    
    seller.set_password("password")
    bidder.set_password("password")
    
    init_database.session.add_all([seller, bidder])
    init_database.session.flush()
    
    item = Item(
        name="Required Fields Bid Item",
        minimum_price=100.0,
        current_price=100.0,
        seller_id=seller.id,
        end_time=datetime.utcnow() + timedelta(days=1)
    )
    init_database.session.add(item)
    init_database.session.flush()
    
    # Test missing user_id
    bid1 = Bid(
        item_id=item.id,
        amount=120.0
    )
    init_database.session.add(bid1)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()
    
    init_database.session.rollback()
    
    # Test missing item_id
    bid2 = Bid(
        user_id=bidder.id,
        amount=120.0
    )
    init_database.session.add(bid2)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()
    
    init_database.session.rollback()
    
    # Test missing amount
    bid3 = Bid(
        item_id=item.id,
        user_id=bidder.id
    )
    init_database.session.add(bid3)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()


# =====================
# Bid Model Tests
# =====================

def test_bid_creation(init_database):
    """Test creating bids for an item."""
    # Create users and item
    seller = User(username="bid_seller", email="bid_seller@example.com")
    bidder1 = User(username="bidder1", email="bidder1@example.com")
    bidder2 = User(username="bidder2", email="bidder2@example.com")
    
    seller.set_password("password")
    bidder1.set_password("password")
    bidder2.set_password("password")
    
    init_database.session.add_all([seller, bidder1, bidder2])
    init_database.session.flush()
    
    item = Item(
        name="Antique Watch",
        minimum_price=100.0,
        current_price=100.0,
        seller_id=seller.id,
        end_time=datetime.utcnow() + timedelta(days=1)
    )
    init_database.session.add(item)
    init_database.session.flush()
    
    # Create bids
    bid1 = Bid(item_id=item.id, user_id=bidder1.id, amount=110.0)
    bid2 = Bid(item_id=item.id, user_id=bidder2.id, amount=120.0)
    bid3 = Bid(item_id=item.id, user_id=bidder1.id, amount=130.0)
    
    init_database.session.add_all([bid1, bid2, bid3])
    init_database.session.commit()
    
    # Test bid relationships and ordering
    saved_bids = Bid.query.filter_by(item_id=item.id).order_by(Bid.amount.desc()).all()
    assert len(saved_bids) == 3
    assert saved_bids[0].amount == 130.0
    assert saved_bids[0].bidder.username == "bidder1"
    assert saved_bids[1].amount == 120.0
    assert saved_bids[1].bidder.username == "bidder2"
    
    # Test getting highest bid
    highest_bid = Bid.query.filter_by(item_id=item.id).order_by(Bid.amount.desc()).first()
    assert highest_bid.amount == 130.0
    assert highest_bid.bidder.username == "bidder1"

# =====================
# Expert-Related Tests
# =====================

def test_expert_category(init_database):
    """Test creating and querying expert categories."""
    # Create an expert user
    expert = User(
        username="art_expert", 
        email="art_expert@example.com",
        priority=UserPriority.EXPERT.value
    )
    expert.set_password("password")
    init_database.session.add(expert)
    init_database.session.flush()
    
    # Add expertise
    expertise1 = ExpertCategory(
        user_id=expert.id,
        category="Paintings",
        expertise_description="Specializes in 19th century European paintings"
    )
    expertise2 = ExpertCategory(
        user_id=expert.id,
        category="Sculptures",
        expertise_description="Knowledge of bronze sculptures"
    )
    
    init_database.session.add_all([expertise1, expertise2])
    init_database.session.commit()
    
    # Test retrieving expertise
    saved_expert = User.query.get(expert.id)
    expertise_list = saved_expert.expertise.all()
    assert len(expertise_list) == 2
    assert "Paintings" in [e.category for e in expertise_list]
    assert "Sculptures" in [e.category for e in expertise_list]

def test_expert_availability(init_database):
    """Test creating and querying expert availability slots."""
    # Create an expert user
    expert = User(
        username="avail_expert", 
        email="avail_expert@example.com",
        priority=UserPriority.EXPERT.value
    )
    expert.set_password("password")
    init_database.session.add(expert)
    init_database.session.flush()
    
    # Add availability slots
    now = datetime.utcnow()
    slot1 = ExpertAvailability(
        user_id=expert.id,
        day_of_week="monday",
        start_time=now + timedelta(days=1, hours=9),
        end_time=now + timedelta(days=1, hours=12)
    )
    slot2 = ExpertAvailability(
        user_id=expert.id,
        day_of_week="monday",
        start_time=now + timedelta(days=2, hours=14),
        end_time=now + timedelta(days=2, hours=18)
    )
    
    init_database.session.add_all([slot1, slot2])
    init_database.session.commit()
    
    # Test retrieving availability
    saved_expert = User.query.get(expert.id)
    availability_slots = saved_expert.availability.all()
    assert len(availability_slots) == 2
    
    # Test finding available experts for a time period
    target_time = now + timedelta(days=1, hours=10)
    available_experts = User.query.join(ExpertAvailability).filter(
        ExpertAvailability.start_time <= target_time,
        ExpertAvailability.end_time >= target_time
    ).all()
    
    assert len(available_experts) == 1
    assert available_experts[0].id == expert.id

def test_authentication_request(init_database):
    """Test the authentication request process."""
    # Create users
    seller = User(username="auth_seller", email="auth_seller@example.com")
    expert = User(
        username="auth_expert", 
        email="auth_expert@example.com",
        priority=UserPriority.EXPERT.value
    )
    manager = User(
        username="auth_manager", 
        email="auth_manager@example.com",
        priority=UserPriority.MANAGER.value
    )
    
    seller.set_password("password")
    expert.set_password("password")
    manager.set_password("password")
    
    init_database.session.add_all([seller, expert, manager])
    init_database.session.flush()
    
    # Create an item
    item = Item(
        name="Ancient Artifact",
        minimum_price=500.0,
        current_price=500.0,
        seller_id=seller.id,
        end_time=datetime.utcnow() + timedelta(days=5)
    )
    init_database.session.add(item)
    init_database.session.flush()
    
    # Create authentication request
    auth_request = AuthenticationRequest(
        item_id=item.id,
        requester_id=seller.id,
        status=AuthenticationStatus.PENDING.value
    )
    init_database.session.add(auth_request)
    init_database.session.flush()
    
    # Manager assigns expert to request
    auth_request.expert_id = expert.id
    init_database.session.commit()
    
    # Expert and seller exchange messages
    message1 = AuthenticationMessage(
        request_id=auth_request.id,
        sender_id=expert.id,
        message="Please provide more detailed photos of the artifact."
    )
    message2 = AuthenticationMessage(
        request_id=auth_request.id,
        sender_id=seller.id,
        message="I've uploaded more photos to the listing."
    )
    
    init_database.session.add_all([message1, message2])
    init_database.session.flush()
    
    # Expert approves the item
    auth_request.status = AuthenticationStatus.APPROVED.value
    item.is_authenticated = True
    init_database.session.commit()
    
    # Test relationships and status
    saved_item = Item.query.get(item.id)
    assert saved_item.is_authenticated is True
    assert saved_item.authentication_request.status == AuthenticationStatus.APPROVED.value
    assert saved_item.authentication_request.expert_id == expert.id
    
    # Test message history
    messages = AuthenticationMessage.query.filter_by(request_id=auth_request.id).order_by(AuthenticationMessage.created_at).all()
    assert len(messages) == 2
    assert messages[0].sender_id == expert.id
    assert messages[1].sender_id == seller.id

# =====================
# Payment Tests
# =====================

def test_payment_creation(init_database):
    """Test creating and processing payments."""
    # Create system configuration for fees
    reg_fee_config = SystemConfiguration(
        key="regular_fee_percentage", 
        value="1.0",
        description="Regular fee percentage for auction items"
    )
    auth_fee_config = SystemConfiguration(
        key="authenticated_fee_percentage", 
        value="5.0",
        description="Fee percentage for authenticated items"
    )
    
    init_database.session.add_all([reg_fee_config, auth_fee_config])
    init_database.session.flush()
    
    # Create users
    seller = User(username="payment_seller", email="payment_seller@example.com")
    buyer = User(username="payment_buyer", email="payment_buyer@example.com")
    
    seller.set_password("password")
    buyer.set_password("password")
    
    init_database.session.add_all([seller, buyer])
    init_database.session.flush()
    
    # Create an item that has been sold
    item = Item(
        name="Vintage Record",
        minimum_price=50.0,
        current_price=100.0,  # Final price after bidding
        seller_id=seller.id,
        winner_id=buyer.id,
        status=ItemStatus.SOLD.value,
        end_time=datetime.utcnow() - timedelta(days=1)
    )
    init_database.session.add(item)
    init_database.session.flush()
    
    # Create payment record for a regular (non-authenticated) item
    fee_percentage = float(reg_fee_config.value)
    fee_amount = item.current_price * (fee_percentage / 100)
    
    payment = Payment(
        item_id=item.id,
        buyer_id=buyer.id,
        seller_id=seller.id,
        amount=item.current_price,
        fee_percentage=fee_percentage,
        fee_amount=fee_amount,
        status="pending"
    )
    init_database.session.add(payment)
    init_database.session.flush()
    
    # Complete the payment
    payment.status = "completed"
    payment.completed_at = datetime.utcnow()
    init_database.session.commit()
    
    # Test payment record
    saved_payment = Payment.query.filter_by(item_id=item.id).first()
    assert saved_payment is not None
    assert saved_payment.amount == 100.0
    assert saved_payment.fee_percentage == 1.0
    assert saved_payment.fee_amount == 1.0
    assert saved_payment.status == "completed"
    assert saved_payment.completed_at is not None
    assert saved_payment.buyer_id == buyer.id
    assert saved_payment.seller_id == seller.id

# =====================
# Notification Tests
# =====================

def test_notifications(init_database):
    """Test creating and managing notifications."""
    # Create a user
    user = User(username="notify_user", email="notify_user@example.com")
    user.set_password("password")
    init_database.session.add(user)
    init_database.session.flush()
    
    # Create an item
    item = Item(
        name="Designer Watch",
        minimum_price=200.0,
        current_price=250.0,
        seller_id=user.id,
        end_time=datetime.utcnow() + timedelta(days=1)
    )
    init_database.session.add(item)
    init_database.session.flush()
    
    # Create different types of notifications
    outbid_notification = Notification(
        user_id=user.id,
        item_id=item.id,
        type="outbid",
        message="You have been outbid on Designer Watch"
    )
    
    won_notification = Notification(
        user_id=user.id,
        item_id=item.id,
        type="won",
        message="Congratulations! You won the auction for Designer Watch"
    )
    
    auth_notification = Notification(
        user_id=user.id,
        item_id=item.id,
        type="authentication",
        message="Your item authentication request has been approved"
    )
    
    init_database.session.add_all([outbid_notification, won_notification, auth_notification])
    init_database.session.commit()
    
    # Test retrieving notifications
    all_notifications = Notification.query.filter_by(user_id=user.id).all()
    assert len(all_notifications) == 3
    
    # Test unread notifications
    unread_notifications = Notification.query.filter_by(user_id=user.id, is_read=False).all()
    assert len(unread_notifications) == 3
    
    # Test marking notifications as read
    for notification in unread_notifications:
        notification.is_read = True
    init_database.session.commit()
    
    remaining_unread = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    assert remaining_unread == 0

# =====================
# Watch Functionality Tests
# =====================

def test_watch_functionality(init_database):
    """Test the auction watching functionality."""
    # Create users
    user1 = User(username="watcher1", email="watcher1@example.com")
    user2 = User(username="watcher2", email="watcher2@example.com")
    seller = User(username="watch_seller", email="watch_seller@example.com")
    
    user1.set_password("password")
    user2.set_password("password")
    seller.set_password("password")
    
    init_database.session.add_all([user1, user2, seller])
    init_database.session.flush()
    
    # Create items
    item1 = Item(
        name="Antique Chair",
        minimum_price=300.0,
        current_price=300.0,
        seller_id=seller.id,
        end_time=datetime.utcnow() + timedelta(days=3)
    )
    
    item2 = Item(
        name="Vintage Lamp",
        minimum_price=150.0,
        current_price=150.0,
        seller_id=seller.id,
        end_time=datetime.utcnow() + timedelta(days=2)
    )
    
    init_database.session.add_all([item1, item2])
    init_database.session.flush()
    
    # Users watch items
    user1.watched_items.append(item1)
    user1.watched_items.append(item2)
    user2.watched_items.append(item1)
    
    init_database.session.commit()
    
    # Test user watches
    user1_watches = user1.watched_items.all()
    assert len(user1_watches) == 2
    assert item1 in user1_watches
    assert item2 in user1_watches
    
    user2_watches = user2.watched_items.all()
    assert len(user2_watches) == 1
    assert item1 in user2_watches
    
    # Test item watchers
    item1_watchers = item1.watchers.all()
    assert len(item1_watchers) == 2
    assert user1 in item1_watchers
    assert user2 in item1_watchers
    
    item2_watchers = item2.watchers.all()
    assert len(item2_watchers) == 1
    assert user1 in item2_watchers
    
    # Test removing a watch
    user1.watched_items.remove(item1)
    init_database.session.commit()
    
    updated_user1_watches = user1.watched_items.all()
    assert len(updated_user1_watches) == 1
    assert item1 not in updated_user1_watches
    assert item2 in updated_user1_watches
    
    updated_item1_watchers = item1.watchers.all()
    assert len(updated_item1_watchers) == 1
    assert user1 not in updated_item1_watchers
    assert user2 in updated_item1_watchers

# =====================
# System Configuration Tests
# =====================

def test_system_configuration_creation(init_database):
    """Test creating and retrieving system configuration settings."""
    # Create configuration settings
    configs = [
        SystemConfiguration(
            key="site_name", 
            value="AuctionHub",
            description="Name of the auction site"
        ),
        SystemConfiguration(
            key="contact_email", 
            value="support@auctionhub.com",
            description="Support email address"
        ),
        SystemConfiguration(
            key="minimum_bid_increment", 
            value="5.0",
            description="Minimum increment between bids in dollars"
        )
    ]
    
    init_database.session.add_all(configs)
    init_database.session.commit()
    
    # Test retrieving configuration values
    saved_configs = SystemConfiguration.query.all()
    assert len(saved_configs) >= 3
    
    site_name = SystemConfiguration.query.filter_by(key="site_name").first()
    assert site_name.value == "AuctionHub"
    
    min_bid_increment = SystemConfiguration.query.filter_by(key="minimum_bid_increment").first()
    assert float(min_bid_increment.value) == 5.0

def test_system_configuration_update(init_database):
    """Test updating system configuration settings."""
    # Create a configuration setting
    fee_config = SystemConfiguration(
        key="standard_fee_percentage", 
        value="2.5",
        description="Standard fee percentage for sales"
    )
    
    init_database.session.add(fee_config)
    init_database.session.commit()
    
    # Update the configuration
    saved_config = SystemConfiguration.query.filter_by(key="standard_fee_percentage").first()
    saved_config.value = "3.0"
    init_database.session.commit()
    
    # Verify the update
    updated_config = SystemConfiguration.query.filter_by(key="standard_fee_percentage").first()
    assert updated_config.value == "3.0"
    assert float(updated_config.value) == 3.0

def test_system_configuration_unique_key(init_database):
    """Test that configuration keys must be unique."""
    # Create a configuration
    config1 = SystemConfiguration(
        key="unique_setting", 
        value="original_value",
        description="Test unique constraint"
    )
    
    init_database.session.add(config1)
    init_database.session.commit()
    
    # Try to create another with the same key
    config2 = SystemConfiguration(
        key="unique_setting", 
        value="different_value",
        description="Duplicate key test"
    )
    
    init_database.session.add(config2)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()
    
    init_database.session.rollback()

def test_system_configuration_required_fields(init_database):
    """Test validation of required fields for SystemConfiguration model."""
    # Test missing key
    config1 = SystemConfiguration(
        value="no_key_value",
        description="Missing key configuration"
    )
    
    init_database.session.add(config1)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()
    
    init_database.session.rollback()
    
    # Test missing value
    config2 = SystemConfiguration(
        key="no_value_key",
        description="Missing value configuration"
    )
    
    init_database.session.add(config2)
    
    with pytest.raises(Exception):  # Should raise integrity error
        init_database.session.commit()
    
    init_database.session.rollback()

# =====================
# Database Integrity Tests
# =====================

def test_cascade_delete_user(init_database):
    """Test cascade deletion when a user is deleted."""
    # Create a user with related records
    user = User(username="delete_user", email="delete_user@example.com")
    user.set_password("password")
    
    init_database.session.add(user)
    init_database.session.flush()
    
    # Create an item owned by the user
    item = Item(
        name="User's Item",
        minimum_price=100.0,
        current_price=100.0,
        seller_id=user.id,
        end_time=datetime.utcnow() + timedelta(days=1)
    )
    
    init_database.session.add(item)
    init_database.session.flush()
    
    # Create a notification for the user
    notification = Notification(
        user_id=user.id,
        type="system",
        message="Test notification"
    )
    
    init_database.session.add(notification)
    
    # Create expert-related records if user is an expert
    expertise = ExpertCategory(
        user_id=user.id,
        category="Test Category",
        expertise_description="Test expertise"
    )
    
    availability = ExpertAvailability(
        user_id=user.id,
        day_of_week="Monday",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=2)
    )
    
    init_database.session.add_all([expertise, availability])
    init_database.session.commit()
    
    # Store IDs for later verification
    user_id = user.id
    item_id = item.id
    notification_id = notification.id
    expertise_id = expertise.id
    availability_id = availability.id
    
    # Delete the user
    init_database.session.delete(user)
    init_database.session.commit()
    
    # Verify related records are appropriately handled
    assert User.query.get(user_id) is None
    
    # Check if cascade deletion or nullification happened correctly
    
    # Item might be preserved with seller_id set to NULL, or might be deleted
    saved_item = Item.query.get(item_id)
    if saved_item:
        assert saved_item.seller_id is None
    
    # Expert-related records should typically be deleted
    assert ExpertCategory.query.get(expertise_id) is None
    assert ExpertAvailability.query.get(availability_id) is None
    
    # Notifications should typically be deleted
    assert Notification.query.get(notification_id) is None

def test_cascade_delete_item(init_database):
    """Test cascade deletion when an item is deleted."""
    # Create users
    seller = User(username="cascade_seller", email="cascade_seller@example.com")
    bidder = User(username="cascade_bidder", email="cascade_bidder@example.com")
    
    seller.set_password("password")
    bidder.set_password("password")
    
    init_database.session.add_all([seller, bidder])
    init_database.session.flush()
    
    # Create an item
    item = Item(
        name="Cascade Test Item",
        minimum_price=50.0,
        current_price=50.0,
        seller_id=seller.id,
        end_time=datetime.utcnow() + timedelta(days=1)
    )
    
    init_database.session.add(item)
    init_database.session.flush()
    
    # Create related records
    bid = Bid(
        item_id=item.id,
        user_id=bidder.id,
        amount=60.0
    )
    
    image = ItemImage(
        item_id=item.id,
        image_path="/path/to/test/image.jpg"
    )
    
    auth_request = AuthenticationRequest(
        item_id=item.id,
        requester_id=seller.id,
        status=AuthenticationStatus.PENDING.value
    )
    
    notification = Notification(
        user_id=bidder.id,
        item_id=item.id,
        type="bid",
        message="Your bid was placed successfully"
    )
    
    # Add the item to bidder's watched items
    bidder.watched_items.append(item)
    
    init_database.session.add_all([bid, image, auth_request, notification])
    init_database.session.commit()
    
    # Store IDs for later verification
    item_id = item.id
    bid_id = bid.id
    image_id = image.id
    auth_request_id = auth_request.id
    notification_id = notification.id
    
    # Delete the item
    init_database.session.delete(item)
    init_database.session.commit()
    
    # Verify the item is deleted
    assert Item.query.get(item_id) is None
    
    # Verify related records are appropriately handled
    assert Bid.query.get(bid_id) is None
    assert ItemImage.query.get(image_id) is None
    assert AuthenticationRequest.query.get(auth_request_id) is None
    
    # Check if notifications are handled correctly
    saved_notification = Notification.query.get(notification_id)
    if saved_notification:
        assert saved_notification.item_id is None
    else:
        # If notification was deleted, this will pass
        assert True
    
    # Verify the watch relationship is removed
    assert item not in bidder.watched_items.all()


def test_relationships_integrity(init_database):
    """Test that relationships maintain data integrity."""
    # Create related users and items
    seller = User(username="rel_integrity_seller", email="rel_int_seller@example.com")
    buyer = User(username="rel_integrity_buyer", email="rel_int_buyer@example.com")
    
    seller.set_password("password")
    buyer.set_password("password")
    
    init_database.session.add_all([seller, buyer])
    init_database.session.flush()
    
    item = Item(
        name="Relationship Test Item",
        minimum_price=200.0,
        current_price=200.0,
        seller_id=seller.id,
        end_time=datetime.utcnow() + timedelta(days=1)
    )
    
    init_database.session.add(item)
    init_database.session.flush()
    
    # Create a bid and mark item as sold
    bid = Bid(
        item_id=item.id,
        user_id=buyer.id,
        amount=250.0
    )
    
    init_database.session.add(bid)
    init_database.session.flush()
    
    item.current_price = 250.0
    item.winner_id = buyer.id
    item.status = ItemStatus.SOLD.value
    init_database.session.commit()
    
    # Test integrity of relationships
    saved_item = Item.query.get(item.id)
    saved_bid = Bid.query.get(bid.id)
    
    # Item → seller relationship
    assert saved_item.seller.id == seller.id
    assert saved_item in seller.items_sold.all()
    
    # Item → winner relationship
    assert saved_item.winner.id == buyer.id
    assert saved_item in buyer.items_won.all()
    
    # Bid → user relationship
    assert saved_bid.bidder.id == buyer.id
    assert saved_bid in buyer.bids.all()
    
    # Bid → item relationship
    assert saved_bid.item.id == item.id
    assert saved_bid in item.bids.all()