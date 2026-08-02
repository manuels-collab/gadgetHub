from flask import Blueprint, render_template
from .services import StoreService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    categories = StoreService.get_all_categories()
    featured_products = StoreService.get_featured_products(limit=8)
    product_of_the_week = StoreService.get_product_of_the_week()
    
    return render_template(
        'index.html',
        categories=categories,
        featured_products=featured_products,
        product_of_the_week=product_of_the_week
    )
