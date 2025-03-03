from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

# Enums
class UserPriority(Enum):
    GENERAL_USER = 1
    EXPERT = 2
    MANAGER = 3

class ItemStatus(Enum):
    PENDING = 1
    ACTIVE = 2
    SOLD = 3
    EXPIRED = 4

class AuthenticationStatus(Enum):
    PENDING = 1
    APPROVED = 2
    REJECTED = 3
    SECOND_OPINION = 4

# Association tables
user_watched_auctions = db.Table('user_watched_auctions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('item_id', db.Integer, db.ForeignKey('items.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

# Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    priority = db.Column(db.Integer, default=UserPriority.GENERAL_USER.value)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Card details (optional, for quicker purchase)
    card_number_hash = db.Column(db.String(256))
    card_expiry = db.Column(db.String(10))
    
    # Relationships
    items_sold = db.relationship('Item', backref='seller', lazy='dynamic', foreign_keys='Item.seller_id', cascade="all, delete-orphan")
    items_won = db.relationship('Item', backref='winner', lazy='dynamic', foreign_keys='Item.winner_id', cascade="all, delete-orphan")
    bids = db.relationship('Bid', backref='bidder', lazy='dynamic', cascade="all, delete-orphan")
    watched_items = db.relationship('Item', secondary=user_watched_auctions, lazy='dynamic',
                                   backref=db.backref('watchers', lazy='dynamic'))
    expertise = db.relationship('ExpertCategory', backref='expert', lazy='dynamic', cascade="all, delete-orphan")
    availability = db.relationship('ExpertAvailability', backref='expert', lazy='dynamic', cascade="all, delete-orphan")
    authentication_requests = db.relationship('AuthenticationRequest', backref='expert', lazy='dynamic',
                                             foreign_keys='AuthenticationRequest.expert_id')
    notification = db.relationship('Notification', backref='self', lazy='dynamic', cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_expert(self):
        return self.priority >= UserPriority.EXPERT.value
    
    def is_manager(self):
        return self.priority == UserPriority.MANAGER.value
    
    def __repr__(self):
        return f'<User {self.username}>'


class ExpertCategory(db.Model):
    __tablename__ = 'expert_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category = db.Column(db.String(64), nullable=False)
    expertise_description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ExpertCategory {self.category}>'


class ExpertAvailability(db.Model):
    __tablename__ = 'expert_availability'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ExpertAvailability {self.start_time} to {self.end_time}>'


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    items = db.relationship('Item', backref='category_rel', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'


class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    minimum_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.Integer, default=ItemStatus.PENDING.value)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_authenticated = db.Column(db.Boolean, default=False)
    
    # Relationships
    bids = db.relationship('Bid', backref='item', lazy='dynamic', cascade="all, delete-orphan")
    images = db.relationship('ItemImage', backref='item', lazy='dynamic', cascade="all, delete-orphan")
    authentication_request = db.relationship('AuthenticationRequest', backref='item', uselist=False, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', lazy='dynamic', cascade="all, delete-orphan")
    
    def is_active(self):
        now = datetime.utcnow()
        return (self.status == ItemStatus.ACTIVE.value and 
                self.start_time <= now <= self.end_time)
    
    def time_left(self):
        now = datetime.utcnow()
        if now > self.end_time:
            return 0
        return (self.end_time - now).total_seconds()
    
    def __repr__(self):
        return f'<Item {self.name}>'


class ItemImage(db.Model):
    __tablename__ = 'item_images'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ItemImage for item {self.item_id}>'


class Bid(db.Model):
    __tablename__ = 'bids'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Bid ${self.amount} on item {self.item_id}>'


class AuthenticationRequest(db.Model):
    __tablename__ = 'authentication_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expert_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.Integer, default=AuthenticationStatus.PENDING.value)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('AuthenticationMessage', backref='request', lazy='dynamic')
    requester = db.relationship('User', foreign_keys=[requester_id])
    
    def __repr__(self):
        return f'<AuthenticationRequest for item {self.item_id}>'


class AuthenticationMessage(db.Model):
    __tablename__ = 'authentication_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('authentication_requests.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User')
    
    def __repr__(self):
        return f'<AuthenticationMessage from user {self.sender_id}>'


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    fee_percentage = db.Column(db.Float, nullable=False)
    fee_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    item = db.relationship('Item')
    buyer = db.relationship('User', foreign_keys=[buyer_id])
    seller = db.relationship('User', foreign_keys=[seller_id])
    
    def __repr__(self):
        return f'<Payment ${self.amount} for item {self.item_id}>'


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    type = db.Column(db.String(50), nullable=False)  # outbid, won, ended, authentication
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User')
    item = db.relationship('Item')
    
    def __repr__(self):
        return f'<Notification for user {self.user_id} type {self.type}>'


class SystemConfiguration(db.Model):
    __tablename__ = 'system_configuration'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<SystemConfiguration {self.key}={self.value}>'