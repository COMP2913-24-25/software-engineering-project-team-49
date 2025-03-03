from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from .models import User

class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20, message="Username should be between 3 and 20 characters.")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password should be minimum 6 characters.")])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords should match.")])
    role = SelectField('role', choices=[('1', 'User'), ('2', 'Expert'), ('3', 'Manager')], validators=[DataRequired()])
    submit = SubmitField('Sign Up')
    def validate_username(self, username):
        User = user.query.filter_by(username=username.data).first()
        if User:
            raise ValidationError("Username already taken.")
        
class LogInForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')