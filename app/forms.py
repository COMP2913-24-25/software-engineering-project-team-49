from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DecimalField, TimeField, BooleanField
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, NumberRange
from .models import User, Category

class SignUpForm(FlaskForm):
    first_name= StringField('first name')
    last_name = StringField('last name')
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20, message="Username should be between 3 and 20 characters.")])
    email = StringField('email', validators=[DataRequired(), Length(min = 3, max=100, message="Email should be between 3 and 100 characters")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password should be minimum 6 characters.")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords should match.")])
    submit = SubmitField('Sign Up')
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username already taken.")
        
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
    authentication = SelectField('Atheticate Item (5 percent fee if authenticated)', choices=[('1', 'Yes'), ('2', 'No')])
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
    sunday_start = TimeField("Sunday Start", format='%H%M', validators=[DataRequired()])
    sunday_end = TimeField("Sunday End", format='%H%M', validators=[DataRequired()])
    monday_start = TimeField("Monday Start", format='%H%M', validators=[DataRequired()])
    monday_end = TimeField("Monday End", format='%H%M', validators=[DataRequired()])
    tuesday_start = TimeField("Tuesday Start", format='%H%M', validators=[DataRequired()])
    tuesday_end = TimeField("Tuesday End", format='%H%M', validators=[DataRequired()])
    wednesday_start = TimeField("Wednesday Start", format='%H%M', validators=[DataRequired()])
    wednesday_end = TimeField("Wednesday End", format='%H%M', validators=[DataRequired()])
    thursday_start = TimeField("Thursday Start", format='%H%M', validators=[DataRequired()])
    thursday_end = TimeField("Thursday End", format='%H%M', validators=[DataRequired()])
    friday_start = TimeField("Sunday Start", format='%H%M', validators=[DataRequired()])
    friday_end = TimeField("Sunday Start", format='%H%M', validators=[DataRequired()])
    saturday_start = TimeField("Sunday Start", format='%H%M', validators=[DataRequired()])
    saturday_end = TimeField("Sunday Start", format='%H%M', validators=[DataRequired()])
    disable_week = BooleanField("Take the week off (Holiday/Illness)")
    submit = SubmitField("Set availability")

class SearchForm(FlaskForm):
    query = StringField('Search Auctions', validators=[DataRequired()])
    submit = SubmitField('Search')


class CategoryForm(FlaskForm):
    categories = QuerySelectMultipleField('Select Categories', query_factory=lambda: Category.query.all(), get_label='name')
    submit = SubmitField('Save')