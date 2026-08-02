from sqlalchemy import func
from ..extensions import db
from ..models.models import Category, Product


class StoreService:
    @staticmethod
    def get_all_categories() -> list:
        """Retrieves all available e-commerce product categories from MySQL.
        
        Used to dynamically render the navigation bar menus and category section grids.
        """
        return db.session.execute(db.select(Category).order_by(Category.name.asc())).scalars().all()

    @staticmethod
    def get_featured_products(limit: int = 8) -> list:
        """Retrieves products explicitly marked as featured by systems administrators.
        
        Args:
            limit (int): The maximum number of trending products to display.
        """
        return db.session.execute(
            db.select(Product)
            .filter_by(is_featured=True)
            .order_by(Product.created_at.desc())
            .limit(limit)
        ).scalars().all()

    @staticmethod
    def get_product_of_the_week() -> Product | None:
        """Selects a highly-rated featured product dynamically to act as the Product of the Week spotlight node.
        
        Applies a random sorting algorithm compatible across both SQLite and MySQL backends.
        """
        # Determine the active database engine to apply the correct random SQL function
        random_func = func.random() if db.engine.name == 'sqlite' else func.rand()
        
        return db.session.execute(
            db.select(Product)
            .filter_by(is_featured=True)
            .filter(Product.stock > 0)  # Guarantees the item spotlighted is actively available for cart routing
            .order_by(random_func)
        ).scalars().first()
