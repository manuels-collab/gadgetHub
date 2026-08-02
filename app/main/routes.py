from flask import Blueprint, render_template
from .services import StoreService
from .async_utils import run_blocking

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
async def index():
    categories = await run_blocking(StoreService.get_all_categories)
    featured_products = await run_blocking(lambda: StoreService.get_featured_products(limit=4))
    product_of_the_week = await run_blocking(StoreService.get_product_of_the_week)
    
    return render_template(
        'index.html',
        categories=categories,
        featured_products=featured_products,
        product_of_the_week=product_of_the_week
    )
