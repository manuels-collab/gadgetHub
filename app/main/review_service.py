from datetime import datetime, timezone
from sqlalchemy import func
from ..extensions import db
from ..models.models import Reviews, Product

class ReviewService:
    @staticmethod
    def add_product_review(user_id: int, product_id: int, form_data) -> bool:
        """Saves a customer review and recalculates the product's average rating."""
        # 1. Prevent multiple reviews from the same user on the same product
        already_reviewed = db.session.execute(
            db.select(Reviews).filter_by(user_id=user_id, product_id=product_id)
        ).scalar_one_or_none()
        
        if already_reviewed:
            return False

        # 2. Write the new review trace row to MySQL
        new_review = Reviews(
            user_id=user_id,
            product_id=product_id,
            rating=form_data.rating.data,
            title=form_data.title.data,
            comment=form_data.comment.data,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(new_review)
        db.session.commit()

        # 3. Recalculate and update the Product's average rating aggregate field
        ReviewService.recalculate_product_rating(product_id)
        return True

    @staticmethod
    def recalculate_product_rating(product_id: int):
        """Computes the current rounded average rating of a product across all reviews."""
        avg_rating = db.session.execute(
            db.select(func.avg(Reviews.rating)).filter_by(product_id=product_id)
        ).scalar()
        
        product = db.session.get(Product, product_id)
        if product and avg_rating is not None:
            # Round to the nearest integer to match your Integer column definition
            product.average_rating = int(round(avg_rating))
            db.session.commit()
