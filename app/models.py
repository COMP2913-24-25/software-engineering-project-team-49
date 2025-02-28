from app import db

class user(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Integer, default = 1) #1 = user, 2 = expert 3 = manager

    #relationships
    notifications = db.relationship('notification', back_populates='user', cascade="all, delete-orphan")
    items = db.relationship('item', back_populates='user', cascade="all, delete-orphan")
    bids = db.relationship('bid', back_populates='user', cascade="all, delete-orphan")
    payments = db.relationship('payment', back_populates='user', cascade="all, delete-orphan")
    expertAvailablity = db.relationship('expertAvailablity', back_populates='user', cascade="all, delete-orphan")
    requests = db.relationship('request', back_populates='user', cascade="all, delete-orphan")

class item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(200))
    starting_price= db.Column(db.Integer)
    duration= db.Column(db.Integer)
    auction_end = db.Column(db.DateTime)
    authenticated = db.Column(db.Boolean)

    #foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    #relationships
    bids = db.relationship('bid', back_populates='item')
    payments = db.relationship('payment', back_populates='item')
    requests = db.relationship('request', back_populates = 'item')

class bid(db.Model):
    __tablename__ = 'bids'
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer)
    bid_time = db.Column (db.DateTime)

    #foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id', ondelete="CASCADE"), nullable=False)

    #relationships
    payment = db.relationship('payment', back_populates='bid')


class payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    amount_paid = db.Column(db.Integer)
    payment_status = db.Column(db.Boolean)
    payment_time = db.Column(db.DateTime)

    #foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id', ondelete="CASCADE"), nullable=False)

    #relationships
    bid = db.relationship('bid', back_populates='payment')

class notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(200))
    created_at = db.Column(db.DateTime)
    is_read = db.Column(db.Boolean)

    #foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    #relationships
    request = db.relationship('request', back_populates='notification')

class request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Boolean)
    fee_percentage = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)

    #foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id', ondelete="CASCADE"), nullable=False)
    expert_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    #relationships
    notification = db.relationship('notification')

class expertAvailablity(db.Model):
    __tablename__ = 'experts'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    #foreign keys
    expert_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    #relationships
    request = db.relationship('requests')

class setting(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    value = db.Column(db.Integer)

class report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True)
    week_start = db.Column(db.DateTime)
    week_end = db.Column(db.DateTime)
    total_sales = db.Column(db.Integer)
    total_fees = db.Column(db.Integer)