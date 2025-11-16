from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models to register them
from models.user import User, AuthToken, UserRole
from models.otp_attempt import OTPAttempt
from models.address import Address
from models.product import Product
from models.groupdeal import GroupDeal, GroupDealProduct
from models.order import Order, OrderItem

