from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DecimalField
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
    submit = SubmitField('List Item')

    def __init__(self, *args, **kwargs):
        super(AuctionItemForm, self).__init__(*args, **kwargs)
        self.category.choices = [(c.id, c.name) for c in Category.query.all()]