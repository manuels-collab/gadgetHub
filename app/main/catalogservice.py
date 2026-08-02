from sqlalchemy import or_
from ..extensions import db
from ..models.models import Product, Category, Brand

class CatalogService:
    @staticmethod
    def get_filtered_products(category_slug=None, brand_id=None, search_query=None):
        """Processes complex filtering arrays across categories, brands, and text strings."""
        stmt = db.select(Product)
        
        # 1. Filter by Department URL Slug
        if category_slug:
            stmt = stmt.join(Product.category).filter(Category.slug == category_slug)
            
        # 2. Filter by Manufacturer Entity Identifier
        if brand_id:
            stmt = stmt.filter(Product.brand_id == brand_id)
            
        # 3. Process Text Matrix Searches across titles and descriptions
        if search_query:
            search_pattern = f"%{search_query}%"
            stmt = stmt.filter(
                or_(
                    Product.name.like(search_pattern),
                    Product.description.like(search_pattern)
                )
            )
            
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def get_product_details(product_id: int):
        """Fetches product along with fully integrated image galleries and user reviews."""
        return db.session.get(Product, product_id)

    @staticmethod
    def get_related_products(product: Product, limit: int = 4):
        """Queries alternatives within the same department category, omitting the current item."""
        return db.session.execute(
            db.select(Product)
            .filter(Product.category_id == product.category_id, Product.id != product.id)
            .limit(limit)
        ).scalars().all()
