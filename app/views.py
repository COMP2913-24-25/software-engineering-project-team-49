from flask import Blueprint

views = Blueprint("views", __name__)

from app import models, db
from flask import render_template, flash, request, redirect, url_for
from flask_login import login_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from .forms import SignUpForm, LogInForm, AuctionItemForm, BidItemForm
from .models import User, Item, ItemStatus, Category


@views.route('/')
@views.route('/welcome')
def welcome():
	return render_template('welcome.html')

@views.route('/signup', methods=['GET', 'POST'])
def signup():
	form = SignUpForm()
	if form.validate_on_submit():
		new_user = models.User(first_name = form.first_name.data, last_name = form.last_name.data ,username=form.username.data, email=form.email.data)
		new_user.set_password(form.password.data)
		db.session.add(new_user)
		db.session.commit()
		flash('Account successfully created! You will now be redirected to the login page!')
		return redirect(url_for('views.login'))
	return render_template('signup.html', form=form)

@views.route('/login', methods=['GET', 'POST'])
def login():
	form = LogInForm()
	if form.validate_on_submit():
		User = models.User.query.filter_by(username=form.username.data).first()
		if User.check_password(form.password.data):
			flash('Successfully Logged In!')
			login_user(User)
			return(redirect(url_for('views.home')))
		else:
			flash("Invalid Username or Password. Please try again.")
	return render_template('login.html', form=form)

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
        flash("Item listed successfully!")
        return redirect(url_for('views.home'))

    return render_template('list_items.html', form=form)

@views.route('/auction_list')
def auction_list():
    """ Display only active auctions """
    items = Item.query.filter(Item.status == ItemStatus.ACTIVE.value).all()
    return render_template('auction_list.html', items=items)

@views.route('/search', methods=['GET'])
def search():
    """ Search for auction items by name """
    query = request.args.get('query', '')
    items = Item.query.filter(Item.name.ilike(f"%{query}%")).all()
    return render_template('search_results.html', items=items, query=query)

@views.route('/auction_detail/<int:item_id>', methods=['GET', 'POST'])
def auction_detail(item_id):
    """ Display auction details for a single item """
    item = Item.query.get_or_404(item_id)
    form = BidItemForm(item_price=item.current_price)

    if form.validate_on_submit():
        # Process the bid (ensure it is valid)
        new_bid = form.bid_amount.data
        if new_bid < item.current_price * 1.1:
            flash("Your bid must be at least 10% higher than the current price.", "danger")
        else:
            item.current_price = new_bid
            db.session.commit()
            flash("Bid placed successfully!", "success")
            return redirect(url_for('views.auction_detail', item_id=item.id))

    return render_template('auction_detail.html', item=item, form=form)
