from flask import Blueprint

views = Blueprint("views", __name__)

from app import models, db
from flask import render_template, flash, request, redirect, url_for
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from .forms import SignUpForm, LogInForm, AuctionItemForm, BidItemForm, AvailabilityForm
from .models import User, Item, ItemStatus, Category, Bid, Notification, AuthenticationRequest, ExpertAvailability, UserPriority


@views.route('/')
@views.route('/welcome')
def welcome():
	return render_template('welcome.html')

@views.route('/signup', methods=['GET', 'POST'])
def signup():
	form = SignUpForm()
	if form.validate_on_submit():
		new_user = User(first_name = form.first_name.data, last_name = form.last_name.data ,username=form.username.data, email=form.email.data)
		new_user.set_password(form.password.data)
		db.session.add(new_user)
		db.session.commit()
		flash('Account successfully created! You will now be redirected to the login page!', 'success')
		return redirect(url_for('views.login'))
	return render_template('signup.html', form=form)

@views.route('/login', methods=['GET', 'POST'])
def login():
    form = LogInForm()
    if form.validate_on_submit():
        User = models.User.query.filter_by(username=form.username.data).first()
        if User and User.check_password(form.password.data):
            if User.is_expert():
                flash('Successfully Logged In!', 'success')
                login_user(User)
                return redirect(url_for('views.expert'))
            elif User.is_manager():
                flash('Successfully Logged In!', 'success')
                login_user(User)
                return redirect(url_for('views.manager'))
            else:
                flash('Successfully Logged In!', 'success')
                login_user(User)
                return redirect(url_for('views.home'))
        else:
            flash("Invalid Username or Password. Please try again.", 'danger')
    return render_template('login.html', form=form)

@views.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.welcome'))

@views.route('/home')
def home():
    """ Display homepage with auctions that have 1-2 days left """
    now = datetime.utcnow()
    one_day_from_now = now + timedelta(days=1)
    two_days_from_now = now + timedelta(days=2)

    featured_auctions = Item.query.filter(
        Item.status == ItemStatus.ACTIVE.value,
        Item.end_time >= one_day_from_now,
        Item.end_time <= two_days_from_now
    ).limit(5).all()  # Limit to 5 auctions for now

    return render_template('home.html', featured_auctions=featured_auctions)


@views.route('/list_items', methods=['GET', 'POST'])
@login_required
def list_item():
    form = AuctionItemForm()

    if form.validate_on_submit():
        auction_end_time = datetime.utcnow() + timedelta(days=int(form.duration.data))
        if form.authentication.data == '1':
            new_item = models.Item(
                name=form.name.data,
                description=form.description.data,
                category_id=form.category.data, 
                minimum_price=form.minimum_price.data,
                current_price=form.minimum_price.data,
                seller_id=current_user.id,
                start_time=datetime.utcnow(),
                end_time=auction_end_time,
                status=models.ItemStatus.PENDING.value
            )
            db.session.add(new_item)
            db.session.commit()
            authentication = AuthenticationRequest(
                  item_id = new_item.id,
                  requester_id = current_user.id
            )
            db.session.add(authentication)
            db.session.commit()
        else:
            new_item = models.Item(
                name=form.name.data,
                description=form.description.data,
                category_id=form.category.data, 
                minimum_price=form.minimum_price.data,
                current_price=form.minimum_price.data,
                seller_id=current_user.id,
                start_time=datetime.utcnow(),
                end_time=auction_end_time,
                status=models.ItemStatus.ACTIVE.value
            )
            db.session.add(new_item)
            db.session.commit()
        flash('Item listed successfully!', 'success')
        return redirect(url_for('views.home'))

    return render_template('list_items.html', form=form)

@views.route('/auction_list')
def auction_list():
    """ Display only active auctions"""
    items = Item.query.filter(Item.status == ItemStatus.ACTIVE.value).all()
    return render_template('auction_list.html', items=items)

@views.route('/search', methods=['GET'])
def search():
    """ Search for auction items by name """
    query = request.args.get('query', '').strip()  # Remove leading/trailing spaces
    
    if not query:
        flash("Please enter a search term.", "warning")
        return redirect(url_for('views.auction_list'))  # Redirect if search is empty

    items = Item.query.filter(
        Item.name.ilike(f"%{query}%"), 
        Item.status == ItemStatus.ACTIVE.value  # Only search in active auctions
    ).all()
    
    return render_template('search_results.html', items=items, query=query)

@views.route('/auction_detail/<int:item_id>', methods=['GET', 'POST'])
def auction_detail(item_id):
    """ Display auction details for a single item """
    item = Item.query.get_or_404(item_id)
    form = BidItemForm(item_price=item.current_price)

    if form.validate_on_submit():
        # Process the bid (ensure it is valid)
        new_bid_amount = form.bid_amount.data
        if new_bid_amount < item.current_price * 1.1:
            flash("Your bid must be at least 10% higher than the current price.", "danger")
        else:
            previous_bid = Bid.query.filter(Bid.item_id == item_id).order_by(Bid.amount.desc()).first()
            
            #update item price and new bid
            item.current_price = new_bid_amount
            new_bid = Bid(item_id=item_id, user_id = current_user.id, amount = new_bid_amount)
            db.session.add(new_bid)
            db.session.commit()

            #make notification for previous bidder
            if previous_bid and previous_bid.user_id != current_user.id:
                notification = Notification(
                    user_id=previous_bid.user_id,
                    item_id=item.id,
                    type="outbid",
                    message=f"You have been outbid on '{item.name}'. The new bid is £{new_bid_amount:.2f}.",
                )
                db.session.add(notification)
                db.session.commit()

            flash('Bid placed successfully!', 'success')
            return redirect(url_for('views.auction_detail', item_id=item.id))

    return render_template('auction_detail.html', item=item, form=form)

@views.route('/notifications', methods=['GET'])
@login_required
def notifications():
     notifications = Notification.query.filter(Notification.user_id==current_user.id)
     return render_template('notifications.html', notifications=notifications)

@views.route('/expert', methods=['GET', 'POST'])
@login_required
def expert():
    DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    form = AvailabilityForm()
    if form.validate_on_submit():
        ExpertAvailability.query.filter_by(user_id=current_user.id).delete()
        if form.disable_week.data:
            for day in DAYS_OF_WEEK:
                new_availability = models.ExpertAvailability(user_id=current_user.id,
                                                             day_of_week=day,
                                                             start_time=datetime.strptime("08:00", "%H%M").time(),
                                                             end_time=datetime.strptime("20:00", "%H%M").time(),
                                                             status=models.AvailabilityStatus.UNAVAILABLE
                                                            )
                db.session.add(new_availability)
        else:
            availability_data = {
                "Sunday": (form.sunday_start.data, form.sunday_end.data),
                "Monday": (form.monday_start.data, form.monday_end.data),
                "Tuesday": (form.tuesday_start.data, form.tuesday_end.data),
                "Wednesday": (form.wednesday_start.data, form.wednesday_end.data),
                "Thursday": (form.thursday_start.data, form.thursday_end.data),
                "Friday": (form.friday_start.data, form.friday_end.data),
                "Saturday": (form.saturday_start.data, form.saturday_end.data),
            }
            for day, (start, end) in availability_data:
                new_availability = models.ExpertAvailability(user_id=current_user.id,
                                                             day_of_week=day,
                                                             start_time=start,
                                                             end_time=end,
                                                             status=models.AvailabilityStatus.AVAILABLE
                                                            )
                db.session.add(new_availability)
            db.session.commit()
        flash("Availability Added!", "success")
        return redirect(url_for('views.expert'))
    return render_template('expert.html', form=form)

@views.route('/manager', methods=['GET', 'POST'])
@login_required
def manager():
    pending_items = Item.query.filter_by(status=ItemStatus.PENDING.value).all()
    experts = User.query.filter_by(priority=UserPriority.EXPERT.value).all()
    return render_template('manager.html', items=pending_items, experts=experts)
