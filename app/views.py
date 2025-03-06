from flask import Blueprint

views = Blueprint("views", __name__)

from app import models, db
from flask import render_template, flash, request, redirect, url_for
from flask_login import login_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from .forms import SignUpForm, LogInForm, AuctionItemForm
from .models import User, Item, ItemStatus, Category


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
		flash('Account successfully created! You will now be redirected to the login page!')
		return redirect(url_for('views.login'))
	return render_template('signup.html', form=form)

@views.route('/login', methods=['GET', 'POST'])
def login():
	form = LogInForm()
	if form.validate_on_submit():
		User = User.query.filter_by(username=form.username.data).first()
		if User.check_password(form.password.data):
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