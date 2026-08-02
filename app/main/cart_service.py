from ..extensions import db
from ..models.models import Cart, CartItem, Product

class CartService:
    @staticmethod
    def get_or_create_user_cart(user_id: int) -> Cart:
        """Retrieves the active user cart or provisions a new one if none exists."""
        cart = db.session.execute(
            db.select(Cart).filter_by(user_id=user_id)
        ).scalar_one_or_none()
        
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)
            db.session.commit()
        return cart

    @staticmethod
    def add_item_to_cart(user_id: int, product_id: int, quantity: int = 1) -> bool:
        """Adds an item to the cart or increments volume if it exists, enforcing warehouse stock checks."""
        product = db.session.get(Product, product_id)
        if not product or product.stock < quantity:
            return False  # Block action if out of stock or product is missing

        cart = CartService.get_or_create_user_cart(user_id)
        
        item = db.session.execute(
            db.select(CartItem).filter_by(cart_id=cart.id, product_id=product_id)
        ).scalar_one_or_none()

        if item:
            new_qty = item.quantity + quantity
            if new_qty > product.stock:
                return False  # Stacked volume breaches stock boundaries
            item.quantity = new_qty
        else:
            item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
            db.session.add(item)
            
        db.session.commit()
        return True

    @staticmethod
    def update_item_quantity(user_id: int, product_id: int, quantity: int) -> bool:
        """Modifies row depth directly, clearing the trace if quantity drops to zero."""
        if quantity <= 0:
            return CartService.remove_item_from_cart(user_id, product_id)
            
        cart = CartService.get_or_create_user_cart(user_id)
        item = db.session.execute(
            db.select(CartItem).filter_by(cart_id=cart.id, product_id=product_id)
        ).scalar_one_or_none()
        
        if item:
            product = db.session.get(Product, product_id)
            if quantity > product.stock:
                return False  # Requested item depth exceeds warehouse stocks
            item.quantity = quantity
            db.session.commit()
            return True
        return False

    @staticmethod
    def remove_item_from_cart(user_id: int, product_id: int) -> bool:
        """Drops a targeted selection item completely from the session database cart."""
        cart = CartService.get_or_create_user_cart(user_id)
        item = db.session.execute(
            db.select(CartItem).filter_by(cart_id=cart.id, product_id=product_id)
        ).scalar_one_or_none()
        
        if item:
            db.session.delete(item)
            db.session.commit()
            return True
        return False

    @staticmethod
    def calculate_cart_totals(user_id: int) -> dict:
        """Calculates subtotals, platform taxes, flat shipping rates, and final checkout grand totals."""
        cart = CartService.get_or_create_user_cart(user_id)
        subtotal = 0
        
        for item in cart.cart_item:
            # Fallback to base pricing matrices if discounted_price is unset
            price = item.product.discounted_price if item.product.discounted_price else item.product.price
            subtotal += price * item.quantity
            
        # Free delivery incentives for values exceeding $100 (10000 cents), else standard flat fee of $15
        shipping_fee = 0 if subtotal >= 10000 or subtotal == 0 else 1500
        tax = int(subtotal * 0.05)  # 5% standardized platform tax allocation
        total = subtotal + shipping_fee + tax
        
        return {
            "subtotal": subtotal,
            "shipping_fee": shipping_fee,
            "tax": tax,
            "total": total,
            "items_count": sum(item.quantity for item in cart.cart_item)
        }
