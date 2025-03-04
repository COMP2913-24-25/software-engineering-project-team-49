from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app import models, db

class SignUpForm(FlaskForm):
    first_name= StringField('first name')
    last_name = StringField('last name')
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20, message="Username should be between 3 and 20 characters.")])
    email = StringField('email', validators=[DataRequired(), Length(min = 3, max=100, message="Email should be between 3 and 100 characters")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password should be minimum 6 characters.")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords should match.")])
    submit = SubmitField('Sign Up')
    def validate_username(self, username):
        user = models.User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username already taken.")
        
class LogInForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')