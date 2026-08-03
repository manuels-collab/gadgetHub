import os
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for, abort
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

from .forms import RegisterForm, LoginForm  
from ..extensions import bcrypt, db
from ..models.models import User, Order, Transaction, OrderStatus
from ..main.cart_service import CartService
from ..main.services import StoreService
from ..main.async_utils import run_blocking
from sqlalchemy.exc import IntegrityError


auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
async def register():
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        phone = form.phone.data

        hashed_password = await run_blocking(lambda: bcrypt.generate_password_hash(password).decode('utf-8'))

        image_file = form.profile_image.data
        image_name = None
        if image_file:
            image_name = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), image_name)
            await run_blocking(lambda: image_file.save(upload_path))

        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            profile_image=image_name
        )
        db.session.add(new_user)
        try:
            await run_blocking(lambda: db.session.commit())
            login_user(new_user)
            flash("Registration successful! Welcome to your dashboard.", "success")
            return redirect(url_for('auth.dashboard'))
        except IntegrityError as exc:
            await run_blocking(lambda: db.session.rollback())
            error_text = str(exc).lower()
            if 'username' in error_text:
                form.username.errors.append("This username is already taken.")
            if 'email' in error_text:
                form.email.errors.append("This email is already in use.")
            if not form.username.errors and not form.email.errors:
                flash("That username or email is already taken. Please choose another.", "danger")
        except Exception:
            await run_blocking(lambda: db.session.rollback())
            flash("Registration failed. Please try again or contact support.", "danger")

    return render_template('register.html', form=form)


@auth.route('/register/admin', methods=['GET', 'POST'])
async def register_admin():
    """Hidden admin registration endpoint. Use an obscure URL to avoid accidental discovery."""
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        phone = form.phone.data

        hashed_password = await run_blocking(lambda: bcrypt.generate_password_hash(password).decode('utf-8'))

        image_file = form.profile_image.data
        image_name = None
        if image_file:
            image_name = secure_filename(image_file.filename)
            upload_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), image_name)
            await run_blocking(lambda: image_file.save(upload_path))

        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            profile_image=image_name,
            is_admin=True
        )
        db.session.add(new_user)
        try:
            await run_blocking(lambda: db.session.commit())
            login_user(new_user)
            flash("Administrator registered and logged in.", "success")
            return redirect(url_for('admin.dashboard'))
        except IntegrityError as exc:
            await run_blocking(lambda: db.session.rollback())
            error_text = str(exc).lower()
            if 'username' in error_text:
                form.username.errors.append("This username is already taken.")
            if 'email' in error_text:
                form.email.errors.append("This email is already in use.")
            if not form.username.errors and not form.email.errors:
                flash("That username or email already exists.", "danger")
        except Exception:
            await run_blocking(lambda: db.session.rollback())
            flash("Failed to create admin account.", "danger")

    return render_template('admin_register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
async def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = await run_blocking(lambda: db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none())

        if not user:
            flash("No account found with that email. Please register or check your email.", "danger")
        elif not await run_blocking(lambda: bcrypt.check_password_hash(user.password_hash, password)):
            flash("Incorrect password. Please try again.", "danger")
        else:
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for('auth.dashboard'))
            
    return render_template('login.html', form=form)


@auth.route('/login/admin', methods=['GET', 'POST'])
async def login_admin():
    """Hidden admin login endpoint. Hand-typed URL only."""
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = await run_blocking(lambda: db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none())
        if not user:
            flash("No administrator account found with that email.", "danger")
        elif not await run_blocking(lambda: bcrypt.check_password_hash(user.password_hash, password)):
            flash("Incorrect admin password. Please try again.", "danger")
        elif not getattr(user, 'is_admin', False):
            flash("Access denied. This login is for administrators only.", "danger")
        else:
            login_user(user)
            flash("Admin logged in.", "success")
            return redirect(url_for('admin.dashboard'))
    return render_template('admin_login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('auth.login'))

@auth.route('/dashboard')
@login_required
def dashboard():
    cart_totals = CartService.calculate_cart_totals(current_user.id)
    customer_metrics = StoreService.get_customer_dashboard_metrics(current_user.id)

    return render_template(
        'dashboard.html',
        user=current_user,
        cart_items=customer_metrics['cart_items'],
        order_count=customer_metrics['order_count'],
        payments_count=customer_metrics['payments_count'],
        total_spent=customer_metrics['total_spent'],
        cart_count=cart_totals['items_count']
    )

@auth.route("/admin")
@login_required
def admin():

    if not current_user.is_admin:
        abort(403)

    return render_template("admin/dashboard.html")