import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = "app/static/uploads"

    PAYSTACK_SECRET_KEY = os.getenv("PAYMENT_SECRET_KEY") or os.getenv("payment_secret_key")
    PAYSTACK_PUBLIC_KEY = os.getenv("PAYMENT_PUBLIC_KEY") or os.getenv("payment_public_key")


class DevelopmentConfig(Config):
    """Development configuration - safe defaults for local work."""
    ENV = 'development'
    DEBUG = True
    # Prefer a dedicated DEV database url, fall back to generic DATABASE_URL, then sqlite.
    SQLALCHEMY_DATABASE_URI = (
        os.getenv('DEV_DATABASE_URL') or
        os.getenv('DATABASE_URL') or
        'sqlite:///dev.db'
    )
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production configuration - secure defaults."""
    ENV = 'production'
    DEBUG = False
    # Production should provide DATABASE_URL via environment.
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_ECHO = False


# Config selection helper
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}