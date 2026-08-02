from ..extensions import db
from ..models.models import Wishlist, Product, CartItem
from ..main.cart_service import CartService

class WishlistService:
    @staticmethod
    def get_user_wishlist(user_id: int) -> list:
        """Retrieves all active wishlist records for a user from MySQL."""
        return db.session.execute(
            db.select(Wishlist).filter_by(user_id=user_id).order_by(Wishlist.created_at.desc())
        ).scalars().all()

    @staticmethod
    def add_to_wishlist(user_id: int, product_id: int) -> bool:
        """Saves a product to a user's wishlist, preventing duplicate record links."""
        product = db.session.get(Product, product_id)
        if not product:
            return False

        # Check if the product already exists inside the user's tracking list
        exists = db.session.execute(
            db.select(Wishlist).filter_by(user_id=user_id, product_id=product_id)
        ).scalar_one_or_none()

        if not exists:
            wish = Wishlist(user_id=user_id, product_id=product_id)
            db.session.add(wish)
            db.session.commit()
        return True

    @staticmethod
    def remove_from_wishlist(user_id: int, product_id: int) -> bool:
        """Deletes a targeted item link record from the user's wishlist."""
        wish = db.session.execute(
            db.select(Wishlist).filter_by(user_id=user_id, product_id=product_id)
        ).scalar_one_or_none()

        if wish:
            db.session.delete(wish)
            db.session.commit()
            return True
        return False

    @staticmethod
    def move_item_to_cart(user_id: int, product_id: int) -> bool:
        """Transfers an item from the wishlist over to the active shopping cart layout container."""
        # 1. First trigger the existing addition service check
        cart_success = CartService.add_item_to_cart(user_id, product_id, quantity=1)
        
        # 2. If successfully added, drop the record from the wishlist tracker
        if cart_success:
            WishlistService.remove_from_wishlist(user_id, product_id)
            return True
        return False
