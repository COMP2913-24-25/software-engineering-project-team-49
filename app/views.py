from flask import Blueprint

views = Blueprint("views", __name__)

from app import models, db
from flask import render_template, flash, request, redirect, url_for
from flask_login import login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import SignUpForm, LogInForm

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
		user = models.User.query.filter_by(username=form.username.data).first()
		if user.check_password(form.password.data):
			flash('Successfully Logged In!')
			login_user(user)
			return(redirect(url_for('views.home')))
		else:
			flash("Invalid Username or Password. Please try again.")
	return render_template('login.html', form=form)

@views.route('/home')
def home():
    return render_template('home.html')