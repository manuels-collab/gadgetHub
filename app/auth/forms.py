import re

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import PasswordField, SelectField, StringField, SubmitField, ValidationError
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, Length, Regexp

from ..extensions import db
from ..models.models import User


class RegisterForm(FlaskForm):
    COUNTRY_CODES = [
        ("", "Select country"),
        ("1", "United States / Canada (+1)"),
        ("44", "United Kingdom (+44)"),
        ("233", "Ghana (+233)"),
        ("234", "Nigeria (+234)"),
        ("27", "South Africa (+27)"),
        ("254", "Kenya (+254)"),
        ("260", "Zambia (+260)"),
        ("971", "United Arab Emirates (+971)"),
    ]

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
    
    country_code = SelectField(
        label="Country Code",
        choices=COUNTRY_CODES,
        validators=[DataRequired(message="Please select a country code.")]
    )

    phone = StringField(
        label="Phone Number",
        validators=[
            DataRequired(message="Phone number is required."),
            Regexp(r'^\d{7,15}$', message="Please enter a valid phone number using digits only.")
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

    def get_phone_number(self):
        country_code = (self.country_code.data or "").strip()
        phone_value = (self.phone.data or "").strip()
        cleaned_phone = re.sub(r"\D", "", phone_value)
        if not cleaned_phone:
            return ""
        if country_code.startswith("+"):
            prefix = country_code
        else:
            prefix = f"+{country_code}" if country_code else ""
        return f"{prefix}{cleaned_phone}" if prefix else cleaned_phone

    def validate_email(self, field):
        normalized_email = field.data.strip().lower()
        field.data = normalized_email

        if not re.fullmatch(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', normalized_email):
            raise ValidationError("Please enter a properly structured email address.")

        existing_user = db.session.execute(
            db.select(User).filter_by(email=normalized_email)
        ).scalar_one_or_none()
        if existing_user:
            raise ValidationError("This email is already in use.")


class LoginForm(FlaskForm):
    email = EmailField(
        label="Email",
        validators=[
            DataRequired(message="Email is required."),
            Email(message="Please enter a valid email address."),
            Regexp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', message="Please enter a properly structured email address.")
        ]
    )
    
    password = PasswordField(
        label="Password",
        validators=[DataRequired(message="Password is required.")]
    )
    
    submit = SubmitField(label="Login")
