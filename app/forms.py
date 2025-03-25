from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DecimalField, TimeField, BooleanField
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, NumberRange, Email, Regexp
from .models import User, Category
from datetime import datetime, timedelta

class SignUpForm(FlaskForm):
    first_name= StringField('first name')
    last_name = StringField('last name')
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20, message="Username should be between 3 and 20 characters.")])
    email = StringField('email', validators=[DataRequired(), Email(message="Invalid email address"), Regexp(r'^[^@]+@[^@]+\.[^@]+$', message="Invalid email format"), Length(min = 3, max=100, message="Email should be between 3 and 100 characters")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password should be minimum 6 characters.")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords should match.")])
    type = SelectField('Are you a user, expert or manager?', choices=[('1', 'User'), ('2', 'Expert'), ('3', 'Manager')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username already taken.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email already taken")
        
class LogInForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class AuctionItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10)])
    category = SelectField('Category', choices=[], validators=[DataRequired()])
    minimum_price = DecimalField('Minimum Price (£)', validators=[DataRequired(), NumberRange(min=0)])
    duration = SelectField('Auction Duration', choices=[('1', '1 Day'), ('2', '2 Days'), ('3', '3 Days'), ('4', '4 Days'), ('5', '5 Days')])
    authentication = SelectField('Autheticate Item (5 percent fee if authenticated)', choices=[('1', 'Yes'), ('2', 'No')])
    image = MultipleFileField('Item Image', validators=[FileAllowed(['jpg','jpeg','png','gif'], 'Only image files are allowed!')])
    submit = SubmitField('List Item')

    def __init__(self, *args, **kwargs):
        super(AuctionItemForm, self).__init__(*args, **kwargs)
        self.category.choices = [(c.id, c.name) for c in Category.query.all()]

class BidItemForm(FlaskForm):
    bid_amount = DecimalField('Bid Amount', validators=[DataRequired()])
    submit = SubmitField('Place Bid')

    def __init__(self, item_price=None, *args, **kwargs):
        super(BidItemForm, self).__init__(*args, **kwargs)
        self.item_price = item_price  # Store item price for validation

    def validate_bid_amount(self, field):
        min_bid = self.item_price * 1.1 if self.item_price else 0
        if field.data < min_bid:
            raise ValidationError(f"Bid must be at least £{min_bid:.2f}.")

class AvailabilityForm(FlaskForm):
    sunday_start = TimeField("Sunday Start", format='%H:%M', validators=[DataRequired()])
    sunday_end = TimeField("Sunday End", format='%H:%M', validators=[DataRequired()])
    monday_start = TimeField("Monday Start", format='%H:%M', validators=[DataRequired()])
    monday_end = TimeField("Monday End", format='%H:%M', validators=[DataRequired()])
    tuesday_start = TimeField("Tuesday Start", format='%H:%M', validators=[DataRequired()])
    tuesday_end = TimeField("Tuesday End", format='%H:%M', validators=[DataRequired()])
    wednesday_start = TimeField("Wednesday Start", format='%H:%M', validators=[DataRequired()])
    wednesday_end = TimeField("Wednesday End", format='%H:%M', validators=[DataRequired()])
    thursday_start = TimeField("Thursday Start", format='%H:%M', validators=[DataRequired()])
    thursday_end = TimeField("Thursday End", format='%H:%M', validators=[DataRequired()])
    friday_start = TimeField("Friday Start", format='%H:%M', validators=[DataRequired()])
    friday_end = TimeField("Friday Start", format='%H:%M', validators=[DataRequired()])
    saturday_start = TimeField("Saturday Start", format='%H:%M', validators=[DataRequired()])
    saturday_end = TimeField("Saturday Start", format='%H:%M', validators=[DataRequired()])
    submit = SubmitField("Set availability")

class UnavailableForm(FlaskForm):
    disable_week = BooleanField("Take the week off (Holiday/Illness)")
    submit = SubmitField("Set availability")

class SearchForm(FlaskForm):
    query = StringField('Search Auctions', validators=[DataRequired()])
    submit = SubmitField('Search')

class CategoryForm(FlaskForm):
    expert_categories = QuerySelectMultipleField('Select Categories', query_factory=lambda: Category.query.all(), get_label='name')
    submit = SubmitField('Save')

class AssignExpertForm(FlaskForm):
    expert = SelectField('Select Expert', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign Expert')

class AuthenticateForm(FlaskForm):
    approve = SubmitField("Approve Authenticity")
    reject = SubmitField("Reject Authenticity")
    reject_reason = TextAreaField("Reason for Rejection")

class PaymentForm(FlaskForm):
    card_number = StringField('Card Number', validators=[DataRequired(), Length(min=16, max=16)])
    expiry_month = SelectField('Expiry Month', choices=[(str(i), str(i)) for i in range(1, 13)], validators=[DataRequired()])
    expiry_year = SelectField('Expiry Year', choices=[(str(i), str(i)) for i in range(datetime.now().year, datetime.now().year + 11)], validators=[DataRequired()])
    cvv = StringField('CVV', validators=[DataRequired(), Length(min=3, max=4)])
    save_card = SelectField('Save Card', choices=[('1', 'Yes'), ('2', 'No')])
    submit = SubmitField('Pay Now')

class ConfigFeeForm(FlaskForm):
    default_fee = DecimalField('Default fee percentage is 1%', validators=[DataRequired(), NumberRange(min=0, max=100)], places=2)
    expert_fee = DecimalField('Expert Approved fee percenatge is 5%', validators=[DataRequired(), NumberRange(min=0, max=100)], places=2)
    submit = SubmitField('Submit')

class AccountUpdateForm(FlaskForm):
    first_name = StringField('First Name', validators=[Length(max=64)])
    last_name = StringField('Last Name', validators=[Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Length(max=120)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    submit = SubmitField('Update Profile')

    def __init__(self, current_user, *args, **kwargs):
        super(AccountUpdateForm, self).__init__(*args, **kwargs)
        self.current_user = current_user

    def validate_username(self, username):
        # Check if username is different from current username
        if username.data != self.current_user.username:
            # Check if username already exists
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        # Check if email is different from current email
        if email.data != self.current_user.email:
            # Check if email already exists
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already taken. Please choose a different one.')