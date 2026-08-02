from flask import Blueprint, flash, redirect, render_template, request, abort, url_for
from flask_login import current_user

from app.catalog.forms import ReviewForm
from ..main.catalogservice import CatalogService
from ..main.storeservice import StoreService # Reuses the layout fetchers we built
from ..extensions import db
from ..models.models import Brand
from ..main.review_service import ReviewService
catalog_bp = Blueprint('catalog', __name__)

@catalog_bp.route('/products')
@catalog_bp.route('/category/<string:category_slug>')
def product_listing(category_slug=None):
    """Unified endpoint processing showroom grids, filters, and global multi-string lookups."""
    # Read incoming request parameters
    brand_id = request.args.get('brand', type=int)
    search_query = request.args.get('q', type=str)
    
    # Process queries using service models
    products = CatalogService.get_filtered_products(
        category_slug=category_slug, 
        brand_id=brand_id, 
        search_query=search_query
    )
    
    categories = StoreService.get_all_categories()
    brands = db.session.execute(db.select(Brand)).scalars().all()
    
    return render_template(
        "catalog/listing.html",
        products=products,
        categories=categories,
        brands=brands,
        current_category=category_slug,
        current_brand=brand_id,
        search_query=search_query
    )



@catalog_bp.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_details(product_id):
    """Renders comprehensive catalog profile pages with live review modules."""
    product = CatalogService.get_product_details(product_id) or abort(404)
    related_products = CatalogService.get_related_products(product, limit=4)
    
    # Instantiate the review form instance configuration
    form = ReviewForm()

    # Process form submission if the user is authenticated
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You must be logged in to leave a review.", "warning")
            return redirect(url_for('auth.login'))
            
        success = ReviewService.add_product_review(current_user.id, product_id, form)
        if success:
            flash("Thank you! Your product review has been published.", "success")
        else:
            flash("You have already submitted a review for this product.", "danger")
            
        return redirect(url_for('catalog.product_details', product_id=product.id))

    return render_template(
        "catalog/details.html",
        product=product,
        related_products=related_products,
        form=form
    )