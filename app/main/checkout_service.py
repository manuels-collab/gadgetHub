import random
import secrets
import string
from datetime import datetime, timezone
from ..extensions import db
from ..models.models import Cart, CartItem, ShippingAddress, Order, OrderItem, Product, Transaction, OrderStatus, PaymentStatus
from ..main.cart_service import CartService

class CheckoutService:
    @staticmethod
    def generate_order_number() -> str:
        """Generates a unique alphanumeric reference string for a new order."""
        timestamp = datetime.now(timezone.utc).strftime('%Y%M%d')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"ORD-{timestamp}-{random_str}"

    @staticmethod
    def save_shipping_address(user_id: int, form_data) -> ShippingAddress:
        """Saves or creates a shipping destination record for the current user."""
        address = ShippingAddress(
            user_id=user_id,
            full_name=form_data.get('full_name'),
            phone=form_data.get('phone'),
            address=form_data.get('address'),
            city=form_data.get('city'),
            state=form_data.get('state'),
            country=form_data.get('country'),
            postal_code=form_data.get('postal_code')
        )
        db.session.add(address)
        db.session.commit()
        return address

    @staticmethod
    def create_payment_reference() -> str:
        """Generates a unique Paystack transaction reference."""
        random_part = secrets.token_hex(8).upper()
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        return f"PSK-{timestamp}-{random_part}"

    @staticmethod
    def create_pending_order(user_id: int, address_id: int, financials: dict) -> Order:
        """Creates an unpaid order record and preserves cart data until payment is confirmed."""
        order = Order(
            user_id=user_id,
            address_id=address_id,
            order_number=CheckoutService.generate_order_number(),
            subtotal=financials['subtotal'],
            shipping_fee=financials['shipping_fee'],
            discount=0,
            tax=financials['tax'],
            total=financials['total'],
            status=OrderStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(order)
        db.session.flush()

        cart = CartService.get_or_create_user_cart(user_id)
        for item in cart.cart_item:
            price = item.product.discounted_price if item.product.discounted_price else item.product.price
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=price
            )
            db.session.add(order_item)

        db.session.commit()
        return order

    @staticmethod
    def create_pending_transaction(order_id: int, reference: str, amount: int) -> Transaction:
        """Records a pending Paystack transaction linked to an order."""
        transaction = Transaction(
            order_id=order_id,
            reference=reference,
            payment_method='Paystack',
            amount=amount,
            currency='NGN',
            status=PaymentStatus.PENDING,
            gateway='Paystack'
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction

    @staticmethod
    def finalize_paystack_payment(reference: str) -> Order | None:
        """Marks Paystack payment success, updates order status, reduces stock, and clears the cart."""
        transaction = db.session.execute(
            db.select(Transaction).filter_by(reference=reference)
        ).scalar_one_or_none()
        if not transaction:
            return None

        order = db.session.get(Order, transaction.order_id)
        if not order or order.status == OrderStatus.PAID:
            return order

        cart = CartService.get_or_create_user_cart(order.user_id)
        for item in cart.cart_item:
            product = db.session.get(Product, item.product_id)
            if product and product.stock >= item.quantity:
                product.stock -= item.quantity

        transaction.status = PaymentStatus.SUCCESSFUL
        order.status = OrderStatus.PAID
        order.total = order.total
        db.session.commit()

        for item in list(cart.cart_item):
            db.session.delete(item)
        db.session.commit()

        return order

    @staticmethod
    def mark_payment_failed(reference: str) -> None:
        """Marks a Paystack transaction as failed and optionally cancels the order."""
        transaction = db.session.execute(
            db.select(Transaction).filter_by(reference=reference)
        ).scalar_one_or_none()
        if not transaction:
            return

        transaction.status = PaymentStatus.FAILED
        order = db.session.get(Order, transaction.order_id)
        if order:
            order.status = OrderStatus.CANCELLED
        db.session.commit()

    @staticmethod
    def process_order_placement(user_id: int, address_id: int, financials: dict) -> Order | None:
        """Creates an order record, drops matching cart items, and reduces inventory stock quantities."""
        # 1. Fetch user's cart items
        from ..main.cart_service import CartService
        cart = CartService.get_or_create_user_cart(user_id)
        
        if not cart.cart_item:
            return None

        # 2. Check and reduce stock levels across items
        for item in cart.cart_item:
            if item.product.stock < item.quantity:
                return None  # Block checkout if an item sells out mid-transaction

        # 3. Provision the main Order model record
        order = Order(
            user_id=user_id,
            address_id=address_id,
            order_number=CheckoutService.generate_order_number(),
            subtotal=financials['subtotal'],
            shipping_fee=financials['shipping_fee'],
            discount=0, # Can be expanded with coupon calculations later
            tax=financials['tax'],
            total=financials['total'],
            status="Pending",
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(order)
        db.session.flush() # Generates order.id preemptively for foreign keys

        # 4. Migrate line entries and reduce inventory stock level values
        for item in cart.cart_item:
            price = item.product.discounted_price if item.product.discounted_price else item.product.price
            
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=price
            )
            db.session.add(order_item)
            
            # CRITICAL REQUIREMENT: Reduce active warehouse stock depth levels
            item.product.stock -= item.quantity

        # 5. Clear the customer's active shopping cart items completely
        for item in list(cart.cart_item):
            db.session.delete(item)

        db.session.commit()
        return order
