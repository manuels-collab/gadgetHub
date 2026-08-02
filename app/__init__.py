from flask import Flask, redirect, url_for
from .extensions import db, bcrypt, login_manager, csrf, migrate
from sqlalchemy.engine import URL
import os

connection_string = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv('DB_HOST'),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME")
)

from .models.models import (
    User,
    Category,
    Brand,
    Product,
    ProductImage,
    Cart,
    CartItem,
    Wishlist,
    ShippingAddress,
    Order,
    OrderItem,
    Transaction,
    Reviews,
    Coupon,
    NewsletterSubscription,
)

from .main.cart_service import CartService
from flask_login import current_user



def create_app():
    app = Flask(__name__)


    app.config.from_object("config.Config")
    app.config["SQLALCHEMY_ECHO"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = connection_string
    

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"  # type: ignore
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    from .auth.routes import auth
    from .main.routes import main_bp
    from .admin.routes import admin_bp
    from .catalog.routes import catalog_bp
    from .cart.routes import cart_bp
    from .wishlist.routes import wishlist_bp
    from .checkout.routes import checkout_bp
    app.register_blueprint(auth)
    app.register_blueprint(cart_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(wishlist_bp)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def test():
        return redirect(url_for("auth.dashboard"))

    @app.context_processor
    def inject_cart_count():
        """Globally injects the live shopping cart items count into all template headers."""
        if current_user and current_user.is_authenticated:
            totals = CartService.calculate_cart_totals(current_user.id)
            return dict(global_cart_count=totals["items_count"])
        return dict(global_cart_count=0)

    from .main.cart_service import CartService
    from app.models.models import Wishlist
    from sqlalchemy import func

    @app.context_processor
    def inject_global_navbar_counters():
        if current_user and current_user.is_authenticated:
            cart_totals = CartService.calculate_cart_totals(current_user.id)
            
            wishlist_count = db.session.execute(
                db.select(func.count(Wishlist.id)).filter_by(user_id=current_user.id)
            ).scalar() or 0
            
            return dict(
                global_cart_count=cart_totals["items_count"],
                global_wishlist_count=wishlist_count
            )
        return dict(global_cart_count=0, global_wishlist_count=0)

    return app

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
