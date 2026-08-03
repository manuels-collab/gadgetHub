from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import IntegerField, SelectField, StringField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, NumberRange, Length

class ProductForm(FlaskForm):
    name = StringField(label="Product Name", validators=[DataRequired(), Length(max=50)])
    description = TextAreaField(label="Description", validators=[DataRequired(), Length(max=1500)])
    price = IntegerField(label="Base Price (In Naira)", validators=[DataRequired(), NumberRange(min=1)])
    discounted_price = IntegerField(label="Discounted Price (In Naira)", validators=[NumberRange(min=0)])
    stock = IntegerField(label="Stock Quantity", validators=[DataRequired(), NumberRange(min=0)])
    sku = IntegerField(label="SKU Code", validators=[DataRequired()])
    is_featured = BooleanField(label="Mark as Featured", default=True)
    image = FileField(label="Product Thumbnail", validators=[FileAllowed(["jpg", "jpeg", "png", "webp", "jfif", "gif", "bmp", "svg"], message="Only image files are allowed.")])
    brand_id = SelectField(label="Assign Brand", coerce=int, validators=[DataRequired()])
    category_id = SelectField(label="Assign Category", coerce=int, validators=[DataRequired()])
    submit = SubmitField(label="Save Asset Changes")

class CategoryForm(FlaskForm):
    name = StringField(label="Category Name", validators=[DataRequired(), Length(max=50)])
    description = TextAreaField(label="Description", validators=[DataRequired(), Length(max=1500)])
    slug = StringField(label="URL Slug (lowercase-no-spaces)", validators=[DataRequired(), Length(max=50)])
    submit = SubmitField(label="Publish Category")

class BrandForm(FlaskForm):
    name = StringField(label="Brand Name", validators=[DataRequired(), Length(max=50)])
    country = StringField(label="Country of Origin", validators=[DataRequired(), Length(max=40)])
    logo = FileField(label="Brand Logo Image", validators=[FileAllowed(["jpg", "jpeg", "png", "webp", "jfif", "gif", "bmp", "svg"], message="Only image files are allowed.")])
    submit = SubmitField(label="Register Brand")

class ProductImageForm(FlaskForm):
    image = FileField(
        label="Select Gallery Image", 
        validators=[
            FileRequired(message="Please select a file."),
            FileAllowed(["jpg", "jpeg", "png", "webp", "jfif"], message="Images only (JPG, PNG, WEBP, JFIF).")
        ]
    )
    submit = SubmitField(label="Upload to Gallery")
