from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import PasswordField, StringField, SubmitField, ValidationError
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, Length, Regexp

from ..extensions import db
from ..models.models import User


class RegisterForm(FlaskForm):
    username = StringField(
        label="Username",
        validators=[
            DataRequired(message="Username is required."),
            Length(min=3, max=25, message="Username must be between 3 and 25 characters."),
            Regexp(r'^[\w.]+$', message="Username can only contain letters, numbers, underscores, and dots.")
        ]
    )
    
    email = EmailField(
        label="Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address.")
        ]
    )
    
    password = PasswordField(
        label="Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=8, message="Password must be at least 8 characters long.")
        ]
    )
    
    first_name = StringField(
        label="First Name",
        validators=[DataRequired(message="First name is required.")]
    )
    
    last_name = StringField(
        label="Last Name",
        validators=[DataRequired(message="Last name is required.")]
    )
    
    phone = StringField(
        label="Phone Number",
        validators=[
            DataRequired(message="Phone number is required."),
            Regexp(r'^\+?[1-9]\d{1,14}$', message="Please enter a valid international phone number.")
        ]
    )
    
    profile_image = FileField(
        label="Profile Image",
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'jfif', 'gif', 'bmp', 'svg'], message="Only image files are allowed.")
        ]
    )
    
    submit = SubmitField(label="Register")

    def validate_username(self, field):
        existing_user = db.session.execute(
            db.select(User).filter_by(username=field.data)
        ).scalar_one_or_none()
        if existing_user:
            raise ValidationError("This username is already taken.")

    def validate_email(self, field):
        existing_user = db.session.execute(
            db.select(User).filter_by(email=field.data)
        ).scalar_one_or_none()
        if existing_user:
            raise ValidationError("This email is already in use.")


class LoginForm(FlaskForm):
    email = EmailField(
        label="Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address.")
        ]
    )
    
    password = PasswordField(
        label="Password",
        validators=[DataRequired(message="Password is required.")]
    )
    
    submit = SubmitField(label="Login")
