from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..main.cart_service import CartService

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/')
@login_required
def view_cart():
    """Renders the primary interactive shopping cart page summary ledger panel."""
    cart = CartService.get_or_create_user_cart(current_user.id)
    financials = CartService.calculate_cart_totals(current_user.id)
    return render_template("cart/view.html", cart=cart, **financials)


@cart_bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Intercepts execution payloads triggered from showroom or detail item listings."""
    quantity = request.form.get('quantity', default=1, type=int)
    
    success = CartService.add_item_to_cart(current_user.id, product_id, quantity)
    if success:
        flash("Product added to your shopping cart context!", "success")
    else:
        flash("Action denied. Requested allocation volume breaches active stock levels.", "danger")
        
    return redirect(request.referrer or url_for('cart.view_cart'))


@cart_bp.route('/update/<int:product_id>', methods=['POST'])
@login_required
def update_quantity(product_id):
    """Synchronizes field tracking adjustments natively with your MySQL row items."""
    quantity = request.form.get('quantity', type=int)
    
    if quantity is not None:
        success = CartService.update_item_quantity(current_user.id, product_id, quantity)
        if not success:
            flash("Sync issue. Volume requested crosses total item limits.", "danger")
        else:
            flash("Shopping cart item deep parameters updated.", "success")
            
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_item(product_id):
    """Completely terminates a line item reference array from your cart structure."""
    CartService.remove_item_from_cart(current_user.id, product_id)
    flash("Item record eliminated from your active layout.", "warning")
    return redirect(url_for('cart.view_cart'))
