from flask import Blueprint
from app import models, db
from flask import render_template, flash, request, redirect, url_for
from flask_login import login_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from .forms import SignUpForm, LogInForm, AuctionItemForm
from .models import Users, Item, ItemStatus, Category

views = Blueprint("views", __name__)

@views.route('/')
@views.route('/welcome')
def welcome():
	return render_template('welcome.html')

@views.route('/signup', methods=['GET', 'POST'])
def signup():
	form = SignUpForm()
	if form.validate_on_submit():
		hashed_password = generate_password_hash(form.password.data)
		new_user = models.User(username=form.username.data, password=hashed_password, role=form.role.data)
		db.session.add(new_user)
		db.session.commit()
		flash('Account successfully created! You will now be redirected to the login page!')
		return redirect(url_for('login'))
	return render_template('signup.html', form=form)

@views.route('/login', methods=['GET', 'POST'])
def login():
	form = LogInForm()
	if form.validate_on_submit():
		User = models.User.query.filter_by(username=form.username.data).first()
		if User and check_password_hash(User.password, form.password.data):
			flash('Successfully Logged In!')
			login_user(User)
			return(redirect(url_for('home')))
		else:
			flash("Invalid Username or Password. Please try again.")
	return render_template('login.html', form=form)

@views.route('/home')
def home():
    return render_template('home.html')

@views.route('/list_item', methods=['GET', 'POST'])
@login_required
def list_item():
    form = AuctionItemForm()
    
    if form.validate_on_submit():
        auction_end_time = datetime.utcnow() + timedelta(days=int(form.duration.data))
        
        new_item = Item(
            name=form.name.data,
            description=form.description.data,
            category_id=form.category.data, 
            minimum_price=form.minimum_price.data,
            current_price=form.minimum_price.data,
            seller_id=current_user.id,
            start_time=datetime.utcnow(),
            end_time=auction_end_time,
            status=ItemStatus.PENDING.value
        )

        db.session.add(new_item)
        db.session.commit()
        flash("Item listed successfully!")
        return redirect(url_for('views.home'))

    return render_template('list_item.html', form=form)
