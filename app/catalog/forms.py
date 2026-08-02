from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length

class ReviewForm(FlaskForm):
    """Form to submit product feedback and numerical star ratings."""
    rating = IntegerField(
        label="Rating (1-5 Stars)",
        validators=[
            DataRequired(message="Please select a star rating."),
            NumberRange(min=1, max=5, message="Rating must be between 1 and 5.")
        ]
    )
    title = StringField(
        label="Review Title",
        validators=[DataRequired(message="Please enter a brief title."), Length(max=50)]
    )
    comment = TextAreaField(
        label="Your Comments",
        validators=[DataRequired(message="Please share your experience."), Length(max=500)]
    )
    submit = SubmitField(label="Submit Review")
