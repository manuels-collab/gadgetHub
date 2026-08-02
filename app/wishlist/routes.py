from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..main.wishlist_service import WishlistService

wishlist_bp = Blueprint('wishlist', __name__, url_prefix='/wishlist')

@wishlist_bp.route('/')
@login_required
def view_wishlist():
    """Renders the user's active baseline favorite saved item rows panel."""
    wishes = WishlistService.get_user_wishlist(current_user.id)
    return render_template("wishlist/view.html", wishes=wishes)


@wishlist_bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add(product_id):
    """Processes saving a catalog asset link to your wishlist."""
    WishlistService.add_to_wishlist(current_user.id, product_id)
    flash("Item successfully pinned to your wishlist collection!", "success")
    return redirect(request.referrer or url_for('wishlist.view_wishlist'))


@wishlist_bp.route('/remove/<int:product_id>', methods=['POST'])
@login_required
def remove(product_id):
    """Drops an absolute reference trace row link from favorites."""
    WishlistService.remove_from_wishlist(current_user.id, product_id)
    flash("Item record eliminated from your wishlist overview.", "warning")
    return redirect(url_for('wishlist.view_wishlist'))


@wishlist_bp.route('/move-to-cart/<int:product_id>', methods=['POST'])
@login_required
def move_to_cart(product_id):
    """Migrates an item element forward into active purchasing baskets."""
    success = WishlistService.move_item_to_cart(current_user.id, product_id)
    if success:
        flash("Item transferred forward into your active shopping cart!", "success")
        return redirect(url_for('cart.view_cart'))
    else:
        flash("Transfer denied. Item might be out of stock at this moment.", "danger")
        return redirect(url_for('wishlist.view_wishlist'))
