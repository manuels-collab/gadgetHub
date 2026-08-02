import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = True

    UPLOAD_FOLDER = "app/static/uploads"

    PAYSTACK_SECRET_KEY = os.getenv("PAYMENT_SECRET_KEY") or os.getenv("payment_secret_key")
    PAYSTACK_PUBLIC_KEY = os.getenv("PAYMENT_PUBLIC_KEY") or os.getenv("payment_public_key")