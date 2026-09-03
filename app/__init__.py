import os
from flask import Flask, redirect, url_for
from flask_login import current_user
from dotenv import load_dotenv
from sqlalchemy import func
from sqlalchemy.engine import URL

from .extensions import db, bcrypt, login_manager, csrf, migrate
from .models.models import User, Wishlist
from .main.cart_service import CartService

load_dotenv()

# Build connection string fallback for local development
connection_string = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USERNAME"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 5432)),
    database=os.getenv("DB_NAME")
)

def create_app():
    app = Flask(__name__)

    app.config.from_object("config.Config")
    app.config["SQLALCHEMY_ECHO"] = False
    
    # Resolve database URL from environment and adjust driver protocol
    db_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URI")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+psycopg://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or str(connection_string)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"  # type: ignore
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    # Blueprint Registrations
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

    @app.route("/_test")
    def test():
        return redirect(url_for("auth.dashboard"))

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