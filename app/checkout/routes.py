import secrets
import requests
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from ..main.cart_service import CartService
from ..main.checkout_service import CheckoutService

checkout_bp = Blueprint('checkout', __name__, url_prefix='/checkout')

@checkout_bp.route('/', methods=['GET', 'POST'])
@login_required
def place_order():
    """Renders the order summary page and handles order generation details."""
    cart = CartService.get_or_create_user_cart(current_user.id)
    if not cart.cart_item:
        flash("Your shopping cart is empty.", "warning")
        return redirect(url_for('cart.view_cart'))

    financials = CartService.calculate_cart_totals(current_user.id)

    if request.method == 'POST':
        # Collect shipping location data from raw form fields
        form_data = {
            'full_name': request.form.get('full_name'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code')
        }

        # Simple field validation check block
        if not all(form_data.values()):
            flash("All shipping destination parameters are required.", "danger")
            return redirect(url_for('checkout.place_order'))

        # 1. Commit address profile node
        address = CheckoutService.save_shipping_address(current_user.id, form_data)
        
        # 2. Complete order processing matrix and reduce stock
        order = CheckoutService.process_order_placement(current_user.id, address.id, financials)

        if order:
            flash(f"Order {order.order_number} placed successfully!", "success")
            return redirect(url_for('checkout.success_confirmation', order_num=order.order_number))
        else:
            flash("Checkout failed. One or more items in your cart has sold out.", "danger")
            return redirect(url_for('cart.view_cart'))

    return render_template("checkout/order_summary.html", cart=cart, **financials)


@checkout_bp.route('/paystack', methods=['GET', 'POST'])
@login_required
def paystack_checkout():
    cart = CartService.get_or_create_user_cart(current_user.id)
    if not cart.cart_item:
        flash("Your shopping cart is empty.", "warning")
        return redirect(url_for('cart.view_cart'))

    financials = CartService.calculate_cart_totals(current_user.id)

    if request.method == 'POST':
        form_data = {
            'full_name': request.form.get('full_name'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code')
        }

        if not all(form_data.values()):
            flash("All shipping destination parameters are required.", "danger")
            return redirect(url_for('checkout.paystack_checkout'))

        if financials['total'] <= 0:
            flash("Cart total must be greater than zero to proceed with payment.", "danger")
            return redirect(url_for('cart.view_cart'))

        address = CheckoutService.save_shipping_address(current_user.id, form_data)
        order = CheckoutService.create_pending_order(current_user.id, address.id, financials)
        reference = CheckoutService.create_payment_reference()
        CheckoutService.create_pending_transaction(order.id, reference, financials['total'])

        secret_key = current_app.config.get('PAYSTACK_SECRET_KEY')
        if not secret_key:
            flash("Payment gateway is not configured. Contact support.", "danger")
            return redirect(url_for('checkout.paystack_checkout'))

        callback_url = url_for('checkout.paystack_callback', _external=True)
        headers = {
            'Authorization': f'Bearer {secret_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'email': current_user.email,
            'amount': financials['total'] * 100,
            'currency': 'NGN',
            'reference': reference,
            'callback_url': callback_url,
            'metadata': {
                'order_number': order.order_number,
                'user_id': current_user.id
            }
        }

        try:
            response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, json=payload, timeout=20)
            result = response.json()
        except Exception:
            flash("Unable to contact Paystack. Please try again later.", "danger")
            return redirect(url_for('checkout.paystack_checkout'))

        if not result.get('status'):
            flash(result.get('message', 'Unable to initialize payment. Please try again.'), 'danger')
            return redirect(url_for('checkout.paystack_checkout'))

        authorization_url = result['data'].get('authorization_url')
        if not authorization_url:
            flash("Paystack did not return a payment link. Please try again.", "danger")
            return redirect(url_for('checkout.paystack_checkout'))

        return redirect(authorization_url)

    public_key = current_app.config.get('PAYSTACK_PUBLIC_KEY')
    return render_template('checkout/paystack_payment.html', cart=cart, public_key=public_key, **financials)


@checkout_bp.route('/paystack/callback')
@login_required
def paystack_callback():
    reference = request.args.get('reference')
    if not reference:
        flash("Payment callback missing reference.", "danger")
        return redirect(url_for('checkout.payment_failed'))

    secret_key = current_app.config.get('PAYSTACK_SECRET_KEY')
    if not secret_key:
        flash("Payment gateway is not configured. Contact support.", "danger")
        return redirect(url_for('checkout.payment_failed'))

    headers = {
        'Authorization': f'Bearer {secret_key}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers, timeout=20)
        result = response.json()
    except Exception:
        flash("Unable to verify payment. Please contact support.", "danger")
        return redirect(url_for('checkout.payment_failed'))

    if not result.get('status') or result['data'].get('status') != 'success':
        CheckoutService.mark_payment_failed(reference)
        return redirect(url_for('checkout.payment_failed'))

    order = CheckoutService.finalize_paystack_payment(reference)
    if not order:
        flash("Payment was successful but the order update failed. Contact support.", "danger")
        return redirect(url_for('checkout.payment_failed'))

    flash("Payment completed successfully. Your order is confirmed.", "success")
    return redirect(url_for('checkout.success_confirmation', order_num=order.order_number))


@checkout_bp.route('/paystack/failed')
@login_required
def payment_failed():
    return render_template('checkout/payment_failed.html')


@checkout_bp.route('/paystack/cancelled')
@login_required
def payment_cancelled():
    return render_template('checkout/payment_cancelled.html')


@checkout_bp.route('/success/<string:order_num>')
@login_required
def success_confirmation(order_num):
    """Renders a final success view screen confirming order creation."""
    return render_template("checkout/success.html", order_number=order_num)
