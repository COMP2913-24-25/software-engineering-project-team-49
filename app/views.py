from app import app, models, db
from flask import render_template, flash, request, redirect, url_for
from flask_login import login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import SignUpForm, LogInForm

@app.route('/')
@app.route('/welcome')
def welcome():
	return render_template('welcome.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	form = SignUpForm()
	if form.validate_on_submit():
		hashed_password = generate_password_hash(form.password.data)
		new_user = models.user(username=form.username.data, password=hashed_password, role=form.role.data)
		db.session.add(new_user)
		db.session.commit()
		flash('Account successfully created! You will now be redirected to the login page!')
		return redirect(url_for('login'))
	return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LogInForm()
	if form.validate_on_submit():
		User = models.user.query.filter_by(username=form.username.data).first()
		if User and check_password_hash(User.password, form.password.data):
			flash('Successfully Logged In!')
			login_user(User)
			return(redirect(url_for('home')))
		else:
			flash("Invalid Username or Password. Please try again.")
	return render_template('login.html', form=form)