from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.models import Product, Category, Brand, Order, User, ProductImage, Coupon
from .forms import ProductForm, CategoryForm, BrandForm, ProductImageForm
from ..main.services import AdminService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def enforce_admin_guard():
    """Security checkpoint blocking non-admin accounts from all routes in this blueprint."""
    if not current_user.is_admin:
        abort(403)

@admin_bp.route('/')
def dashboard():
    metrics = AdminService.get_dashboard_metrics()
    return render_template("admin/dashboard.html", **metrics)

@admin_bp.route('/products')
def manage_inventory():
    products = db.session.execute(db.select(Product)).scalars().all()
    return render_template("admin/inventory.html", products=products)

@admin_bp.route('/products/add', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()
    form.brand_id.choices = [(b.id, b.name) for b in db.session.execute(db.select(Brand)).scalars().all()]
    form.category_id.choices = [(c.id, c.name) for c in db.session.execute(db.select(Category)).scalars().all()]

    if form.validate_on_submit():
        try:
            AdminService.save_product(form)
            flash("Product published successfully!", "success")
            return redirect(url_for('admin.manage_inventory'))
        except IntegrityError:
            flash("Unable to publish product. A product with that SKU or name may already exist.", "danger")
        except Exception:
            flash("Unable to publish product due to a system error. Please try again.", "danger")
    return render_template("admin/product_form.html", form=form, action="Add")

@admin_bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    product = db.session.get(Product, id) or abort(404)
    form = ProductForm(obj=product)
    form.brand_id.choices = [(b.id, b.name) for b in db.session.execute(db.select(Brand)).scalars().all()]
    form.category_id.choices = [(c.id, c.name) for c in db.session.execute(db.select(Category)).scalars().all()]

    if form.validate_on_submit():
        try:
            AdminService.save_product(form, product_id=id)
            flash("Product updated successfully!", "success")
            return redirect(url_for('admin.manage_inventory'))
        except IntegrityError:
            flash("Unable to update product. A product with that SKU or name may already exist.", "danger")
        except Exception:
            flash("Unable to update product due to a system error. Please try again.", "danger")
    return render_template("admin/product_form.html", form=form, action="Edit")

@admin_bp.route('/products/delete/<int:id>', methods=['POST'])
def delete_product(id):
    if AdminService.delete_product(id):
        flash("Product purged from catalog.", "warning")
    return redirect(url_for('admin.manage_inventory'))


@admin_bp.route('/categories', methods=['GET', 'POST'])
def manage_categories():
    form = CategoryForm()
    if form.validate_on_submit():
        new_cat = Category(name=form.name.data, slug=form.slug.data, description=form.description.data)
        db.session.add(new_cat)
        try:
            db.session.commit()
            flash("New department registered!", "success")
            return redirect(url_for('admin.manage_categories'))
        except IntegrityError as exc:
            db.session.rollback()
            error_text = str(exc).lower()
            if 'unique constraint' in error_text or 'unique violation' in error_text or 'duplicate key' in error_text:
                flash("A category with that name already exists. Please choose another.", "danger")
            else:
                flash("Failed to create category. Please check your input and try again.", "danger")
        except Exception:
            db.session.rollback()
            flash("Failed to create category. Please try again or contact support.", "danger")
    categories = db.session.execute(db.select(Category)).scalars().all()
    return render_template("admin/categories.html", categories=categories, form=form)


@admin_bp.route('/brands', methods=['GET', 'POST'])
def manage_brands():
    form = BrandForm()
    if form.validate_on_submit():
        logo_name = AdminService.process_file_upload(form.logo.data) or "generic-brand.png"
        new_brand = Brand(name=form.name.data, country=form.country.data, logo=logo_name)
        db.session.add(new_brand)
        try:
            db.session.commit()
            flash("Brand registered successfully!", "success")
            return redirect(url_for('admin.manage_brands'))
        except IntegrityError:
            db.session.rollback()
            flash("Failed to create brand. A brand with that name may already exist.", "danger")
        except Exception:
            db.session.rollback()
            flash("Failed to create brand. Please try again.", "danger")
    brands = db.session.execute(db.select(Brand)).scalars().all()
    return render_template("admin/brands.html", brands=brands, form=form)


@admin_bp.route('/brands/edit/<int:id>', methods=['GET', 'POST'])
def edit_brand(id):
    brand = db.session.get(Brand, id) or abort(404)

    form = BrandForm(obj=brand)
    
    if form.validate_on_submit():
        if form.logo.data:
            logo_name = AdminService.process_file_upload(form.logo.data)
            if logo_name:
                brand.logo = logo_name
                
        brand.name = form.name.data
        brand.country = form.country.data
        
        try:
            db.session.commit()
            flash(f"Brand '{brand.name}' updated successfully!", "success")
            return redirect(url_for('admin.manage_brands'))
        except IntegrityError:
            db.session.rollback()
            flash("Failed to update brand. A brand with that name may already exist.", "danger")
        except Exception:
            db.session.rollback()
            flash("Failed to update brand due to a system error.", "danger")
            
    return render_template("admin/brand_form.html", form=form, brand=brand, action="Edit")

@admin_bp.route('/brands/delete/<int:id>', methods=['POST'])
def delete_brand(id):
    brand = db.session.get(Brand, id) or abort(404)
    brand_name = brand.name
    
    db.session.delete(brand)
    try:
        db.session.commit()
        flash(f"Brand '{brand_name}' has been successfully deleted.", "warning")
    except Exception:
        db.session.rollback()
        flash(f"Unable to delete '{brand_name}'. It may be tied to existing active products.", "danger")
        
    return redirect(url_for('admin.manage_brands'))



@admin_bp.route('/orders')
def view_orders():
    orders = db.session.execute(db.select(Order).order_by(Order.created_at.desc())).scalars().all()
    return render_template("admin/orders.html", orders=orders)

@admin_bp.route('/orders/<int:id>')
def view_order(id):
    order = db.session.get(Order, id) or abort(404)
    return render_template("admin/order_details.html", order=order)

@admin_bp.route('/users')
def view_users():
    users = db.session.execute(db.select(User).order_by(User.date_joined.desc())).scalars().all()
    return render_template("admin/users.html", users=users)

@admin_bp.route('/products/<int:product_id>/images', methods=['GET', 'POST'])
@login_required
def manage_product_images(product_id):
    if not current_user.is_admin:
        abort(403)
        
    product = db.session.get(Product, product_id) or abort(404)
    form = ProductImageForm()

    if form.validate_on_submit():
        # Reuse your existing image processor to save the file
        saved_filename = AdminService.process_file_upload(form.image.data)
        
        if saved_filename:
            new_gallery_image = ProductImage(
                product_id=product.id,
                image=saved_filename
            )
            db.session.add(new_gallery_image)
            try:
                db.session.commit()
                flash("Image added to product gallery!", "success")
                return redirect(url_for('admin.manage_product_images', product_id=product.id))
            except Exception:
                db.session.rollback()
                flash("Unable to save gallery image. Please try again.", "danger")

    return render_template("admin/product_images.html", product=product, form=form)

@admin_bp.route('/products/images/delete/<int:image_id>', methods=['POST'])
@login_required
def delete_product_image(image_id):
    if not current_user.is_admin:
        abort(403)
        
    img = db.session.get(ProductImage, image_id) or abort(404)
    product_id = img.product_id
    
    db.session.delete(img)
    db.session.commit()
    flash("Gallery image removed.", "warning")
    return redirect(url_for('admin.manage_product_images', product_id=product_id))


# Assumes your admin_bp is initialized above: admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/coupons', methods=['GET', 'POST'])
def manage_coupons():
    """Renders marketing campaigns index view and processes inline coupon generation inputs."""
    
    # 1. Handle inline POST data inputs for new coupon campaigns
    if request.method == 'POST':
        # Quick validation guard to verify form input text parameters are populated
        code = request.form.get('code')
        discount = request.form.get('discount')
        expiry_date = request.form.get('expiry_date')
        
        if not code or not discount or not expiry_date:
            flash("All coupon generation parameters are required.", "danger")
        else:
            try:
                payload = {
                    'code': code,
                    'discount': discount,
                    'expiry_date': expiry_date
                }
                AdminService.create_coupon(payload)
                flash(f"Campaign code '{code.upper()}' launched successfully!", "success")
                return redirect(url_for('admin.manage_coupons'))
            except IntegrityError:
                flash("This coupon code already exists. Please choose a unique code.", "danger")
            except Exception:
                flash("Failed to generate coupon code. Check format rules and try again.", "danger")
                
    coupons = AdminService.get_all_coupons()
    return render_template("admin/coupons.html", coupons=coupons)


# Ensure OrderStatus is imported in your admin file:
from app.models import db, Order, OrderStatus

@admin_bp.route('/orders/update-status/<int:id>/<string:status>', methods=['POST'])
@login_required
def update_order_status(id, status):
    """Allows administrative control pipelines to toggle order fulfillment parameters."""
    if not current_user.is_admin:
        abort(403)
        
    order = db.session.get(Order, id) or abort(404)
    
    try:
        if status == 'completed':
            order.status = OrderStatus.DELIVERED  # Maps to your Enum 'Delivered' final stage
            flash(f"Order #{order.order_number} has been updated to Delivered.", "success")
        elif status == 'cancelled':
            order.status = OrderStatus.CANCELLED  # Maps to your Enum 'Cancelled'
            flash(f"Order #{order.order_number} has been cancelled successfully.", "warning")
        else:
            flash("Invalid action identifier flag payload status.", "danger")
            return redirect(url_for('admin.view_order', id=order.id))
            
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Database runtime exception mapping updated Enum structures.", "danger")
        
    return redirect(url_for('admin.view_order', id=order.id))

