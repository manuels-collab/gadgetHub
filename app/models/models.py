from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List
from sqlalchemy import String, CheckConstraint, Boolean, DateTime, Integer, ForeignKey, Enum as SQLEnum, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from flask_login import UserMixin
from app.database import Base


class PaymentStatus(str, Enum):
    PENDING = "Pending"
    SUCCESSFUL = "Successful"
    FAILED = "Failed"
    REFUNDED = "Refunded"


class OrderStatus(str, Enum):
    PENDING = "Pending"
    PAID = "Paid"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


class User(Base, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    phone: Mapped[str | None] = mapped_column(String(20))
    profile_image: Mapped[str] = mapped_column(String(40), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    date_joined: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # FIXED: Reordered cascade strings to 'all, delete'
    cart: Mapped['Cart'] = relationship(back_populates='user', cascade='all, delete')
    wishlist: Mapped['Wishlist'] = relationship(back_populates='user', cascade='all, delete')
    ship_address: Mapped[List['ShippingAddress']] = relationship(back_populates='user', cascade='all, delete')
    order: Mapped[List['Order']] = relationship(back_populates='user', cascade='all, delete')


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(1500))
    slug: Mapped[str] = mapped_column(String(50))

    product: Mapped[List['Product']] = relationship(back_populates="category", cascade="all, delete")


class Brand(Base):
    __tablename__ = "brand"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    logo: Mapped[str] = mapped_column(String(40))
    country: Mapped[str] = mapped_column(String(40))

    product: Mapped[List['Product']] = relationship(back_populates="brand", cascade="all, delete")


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(1500))
    price: Mapped[int] = mapped_column(Integer)
    discounted_price: Mapped[int] = mapped_column(Integer)
    stock: Mapped[int] = mapped_column(Integer)
    sku: Mapped[int] = mapped_column(Integer)
    image: Mapped[str] = mapped_column(String(40))
    brand_id: Mapped[int] = mapped_column(ForeignKey("brand.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    average_rating: Mapped[int] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped['Category'] = relationship(back_populates="product")
    brand: Mapped['Brand'] = relationship(back_populates="product")

    product_image: Mapped[List['ProductImage']] = relationship(back_populates='product', cascade="all, delete")
    cart_item: Mapped[List['CartItem']] = relationship(back_populates="product")
    wishlist: Mapped[List['Wishlist']] = relationship(back_populates="product")
    orderitem: Mapped[List['OrderItem']] = relationship(back_populates="product")
    reviews: Mapped[List['Reviews']] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductImage(Base):
    __tablename__ = "product_image"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    image: Mapped[str] = mapped_column(String(50))

    product: Mapped['Product'] = relationship(back_populates="product_image")


class Cart(Base):
    __tablename__ = "cart"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped['User'] = relationship(back_populates="cart")
    cart_item: Mapped[List['CartItem']] = relationship(back_populates='cart', cascade='all, delete')


class CartItem(Base):
    __tablename__ = "cart_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("cart.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    quantity: Mapped[int] = mapped_column(Integer)

    cart: Mapped['Cart'] = relationship(back_populates="cart_item")
    product: Mapped['Product'] = relationship(back_populates="cart_item")


class Wishlist(Base):
    __tablename__ = "wishlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped['User'] = relationship(back_populates="wishlist")
    product: Mapped['Product'] = relationship(back_populates="wishlist")


class ShippingAddress(Base):
    __tablename__ = "shipping_address"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    full_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))
    address: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(30))
    state: Mapped[str] = mapped_column(String(30))
    country: Mapped[str] = mapped_column(String(20))
    postal_code: Mapped[str] = mapped_column(String(10))

    user: Mapped['User'] = relationship(back_populates="ship_address")
    
    order: Mapped[List['Order']] = relationship(back_populates="ship_address")

from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from sqlalchemy import String, CheckConstraint, Integer, ForeignKey, Enum as SQLEnum, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

# Assumes OrderStatus and PaymentStatus Enums are imported or defined above

class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    address_id: Mapped[int] = mapped_column(ForeignKey("shipping_address.id"))
    order_number: Mapped[str] = mapped_column(String(20))
    
    subtotal: Mapped[int] = mapped_column(Integer)
    shipping_fee: Mapped[int] = mapped_column(Integer)
    discount: Mapped[int] = mapped_column(Integer)
    tax: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
    
    status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped['User'] = relationship(back_populates="order")
    ship_address: Mapped['ShippingAddress'] = relationship(back_populates="order")
    orderitem: Mapped[List['OrderItem']] = relationship(back_populates="order", cascade="all, delete-orphan")
    
    # FIXED: Added the missing relationship to satisfy Transaction.order back_populates configuration
    transaction: Mapped['Transaction'] = relationship(back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    
    quantity: Mapped[int] = mapped_column(Integer, nullable=False) 
    price: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)

    order: Mapped['Order'] = relationship(back_populates="orderitem")
    product: Mapped['Product'] = relationship(back_populates="orderitem")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("order.id", ondelete="RESTRICT"))
    reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="NGN", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus), 
        default=PaymentStatus.PENDING, 
        nullable=False
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime,
        insert_default=func.now(), 
        nullable=False
    )
    gateway: Mapped[str] = mapped_column(String(50), nullable=False)

    order: Mapped['Order'] = relationship(back_populates="transaction")


class Reviews(Base):
    __tablename__ = "reviews"

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"))
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(50))
    comment: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: Mapped['User'] = relationship()
    product: Mapped['Product'] = relationship(back_populates="reviews")


class Coupon(Base):
    __tablename__ = "coupons"

    __table_args__ = (
        CheckConstraint("discount > 0", name="check_positive_discount"),
    )

    id: Mapped[int] = mapped_column(primary_key=True) 
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(precision=5, scale=2), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    # FIXED: Added explicit DateTime mapping type
    created_at: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(), nullable=False)

    @property
    def is_valid(self) -> bool:
        # FIXED: Removed timezone.utc restriction so it matches the naive type generated by your form parser
        return self.is_active and self.expiry_date > datetime.now()

class NewsletterSubscription(Base):
    __tablename__ = "newsletter_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # FIXED: Added explicit DateTime mapping type
    subscribed_at: Mapped[datetime] = mapped_column(DateTime, insert_default=func.now(), nullable=False)
