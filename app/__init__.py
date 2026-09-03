import os
from flask import Flask, redirect, url_for
from flask_login import current_user
from sqlalchemy.engine import URL
from sqlalchemy import func

from .extensions import db, bcrypt, login_manager, csrf, migrate
from .models.models import User


def get_database_uri():
    """Dynamically builds and returns the active database connection URI."""
    # 1. Prefer DATABASE_URL or DATABASE_URI if provided by hosting (e.g. Render)
    raw_uri = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URI")
    
    if raw_uri:
        # Convert legacy postgres:// scheme to postgresql:// for SQLAlchemy 2.x
        if raw_uri.startswith("postgres://"):
            return raw_uri.replace("postgres://", "postgresql://", 1)
        return raw_uri

    # 2. Build connection URL from individual DB environment variables if set
    db_host = os.getenv("DB_HOST")
    if db_host:
        port_val = os.getenv("DB_PORT")
        return str(
            URL.create(
                drivername="postgresql+psycopg",
                username=os.getenv("DB_USERNAME"),
                password=os.getenv("DB_PASSWORD"),
                host=db_host,
                port=int(port_val) if port_val else 5432,
                database=os.getenv("DB_NAME"),
            )
        )

    # 3. Local fallback for development
    return "sqlite:///app.db"


def create_app():
    app = Flask(__name__)

    app.config.from_object("config.Config")
    app.config["SQLALCHEMY_ECHO"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()

    print("=" * 60)
    print("SQLALCHEMY_DATABASE_URI:", app.config.get("SQLALCHEMY_DATABASE_URI"))
    print("=" * 60)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"  # type: ignore
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"

    # Blueprints
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

    # Deferred imports for context processors & models
    from .main.cart_service import CartService
    from app.models.models import Wishlist

    @app.route("/_test")
    def test():
        return redirect(url_for("auth.dashboard"))

    @app.context_processor
    def inject_global_navbar_counters():
        """Globally injects cart and wishlist counters into template headers."""
        if current_user and current_user.is_authenticated:
            cart_totals = CartService.calculate_cart_totals(current_user.id)
            
            wishlist_count = (
                db.session.execute(
                    db.select(func.count(Wishlist.id)).filter_by(user_id=current_user.id)
                ).scalar()
                or 0
            )

            return dict(
                global_cart_count=cart_totals["items_count"],
                global_wishlist_count=wishlist_count,
            )
        return dict(global_cart_count=0, global_wishlist_count=0)

    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))