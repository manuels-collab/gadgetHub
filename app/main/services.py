from decimal import Decimal
import os
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from flask import current_app
from sqlalchemy.exc import IntegrityError
from ..extensions import db

from ..models.models import Brand, Category, Product, Order, User, Coupon, Cart, CartItem, Transaction, OrderStatus
from sqlalchemy import func


class StoreService:
    @staticmethod
    def get_all_categories():
        return db.session.execute(
            db.select(Category)
        ).scalars().all()

    @staticmethod
    def get_featured_products(limit: int = 4):
        return db.session.execute(
            db.select(Product)
            .filter_by(is_featured=True)
            .limit(limit)
        ).scalars().all()

    @staticmethod
    def get_product_of_the_week():
        random_func = func.random() if db.engine.name == 'sqlite' else func.random()
        return db.session.execute(
            db.select(Product)
            .filter_by(is_featured=True)
            .order_by(random_func)
        ).scalars().first()





    @staticmethod
    def get_customer_dashboard_metrics(user_id: int) -> dict:
        cart = db.session.execute(db.select(Cart).filter_by(user_id=user_id)).scalar_one_or_none()
        cart_items = sum(item.quantity for item in cart.cart_item) if cart else 0
        order_count = db.session.execute(db.select(func.count(Order.id)).filter_by(user_id=user_id)).scalar() or 0
        payments_count = db.session.execute(
            db.select(func.count(Transaction.id)).join(Order).filter(Order.user_id == user_id)
        ).scalar() or 0
        total_spent = db.session.execute(
            db.select(func.coalesce(func.sum(Order.total), 0)).filter(
                Order.user_id == user_id,
                Order.status != 'Cancelled'
            )
        ).scalar() or 0

        return {
            "cart_items": cart_items,
            "order_count": order_count,
            "payments_count": payments_count,
            "total_spent": total_spent,
        }


class AdminService:
    @staticmethod
    def process_file_upload(file_data) -> str | None:
        if not file_data or not file_data.filename:  # Added safety fallback for empty file names
            return None
        filename = secure_filename(file_data.filename)
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        saved_filename = f"{int(datetime.now(timezone.utc).timestamp())}_{filename}"
        file_data.save(os.path.join(upload_dir, saved_filename))
        return saved_filename

    @staticmethod
    def get_dashboard_metrics() -> dict:
        return {
            "total_users": db.session.execute(db.select(func.count(User.id))).scalar() or 0,
            "gross_revenue": db.session.execute(db.select(func.coalesce(func.sum(Order.total), 0)).filter(Order.status != 'Cancelled')).scalar() or 0,
            "orders_count": db.session.execute(db.select(func.count(Order.id))).scalar() or 0,
            "low_stock_alerts": db.session.execute(db.select(func.count(Product.id)).filter(Product.stock <= 5)).scalar() or 0
        }

    @staticmethod
    def save_product(form, product_id=None) -> Product:
        product = db.session.get(Product, product_id) if product_id else Product()

        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.discounted_price = form.discounted_price.data or form.price.data
        product.stock = form.stock.data
        product.sku = form.sku.data
        product.is_featured = form.is_featured.data
        product.brand_id = form.brand_id.data
        product.category_id = form.category_id.data
        product.updated_at = datetime.now(timezone.utc)

        new_image = AdminService.process_file_upload(form.image.data)
        if new_image:
            product.image = new_image
        elif not product_id:
            product.image = "placeholder.png"

        if not product_id:
            product.average_rating = 5
            product.created_at = datetime.now(timezone.utc)
            db.session.add(product)
            
        try:
            db.session.commit()
            return product
        except IntegrityError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def delete_product(product_id: int) -> bool:
        product = db.session.get(Product, product_id)
        if product:
            db.session.delete(product)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_all_coupons() -> list:
        """Retrieves all promotional coupons from the database order by creation timestamp."""
        return db.session.execute(db.select(Coupon).order_by(Coupon.created_at.desc())).scalars().all()

    @staticmethod
    def create_coupon(form_data) -> Coupon:
        """Creates and commits a brand new promotional discount campaign code to PostgreSQL."""
        # Note: Depending on your choice, if you build a form object for Coupon later,
        # this maps form fields directly into column variables.
        new_coupon = Coupon(
            code=form_data['code'].upper().strip(),
            discount=Decimal(form_data['discount']),
            expiry_date=datetime.strptime(form_data['expiry_date'], '%Y-%m-%d'),
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(new_coupon)
        try:
            db.session.commit()
            return new_coupon
        except IntegrityError:
            db.session.rollback()
            raise
        except Exception:
            db.session.rollback()
            raise

