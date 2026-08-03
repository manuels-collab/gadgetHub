from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from ..main.cart_service import CartService
from ..extensions import db
from ..models.models import Product, Category, Brand, Order, User, ProductImage, Coupon, OrderStatus
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
    """Synchronizes field tracking adjustments natively with your PostgreSQL row items."""
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


@cart_bp.route('/orders')
@login_required
def view_orders():
    """Renders historical orders page for the currently logged-in account."""
    orders = db.session.execute(
        db.select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    ).scalars().all()
    return render_template("my_orders.html", orders=orders)

@cart_bp.route('/orders/cancel/<int:id>', methods=['POST'])
@login_required
def cancel_order(id):
    """Allows a client buyer to safely terminate their pending processing checkout records."""
    order = db.session.get(Order, id) or abort(404)
    
    if order.user_id != current_user.id:
        abort(403)
        

    if order.status not in [OrderStatus.PENDING, OrderStatus.PROCESSING]:
        flash("This order cannot be cancelled because processing has already progressed.", "danger")
        return redirect(url_for('cart.view_orders'))
        
    try:
        # Explicitly assign using your OrderStatus Enum instance
        order.status = OrderStatus.CANCELLED
        db.session.commit()
        flash(f"Order #{order.order_number} successfully cancelled.", "success")
    except Exception:
        db.session.rollback()
        flash("System error running cancellation update framework parameters.", "danger")
        
    return redirect(url_for('cart.view_orders'))
