from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models to register them
from models.user import User, AuthToken, UserRole
from models.otp_attempt import OTPAttempt
from models.address import Address
from models.product import Product
from models.groupdeal import GroupDeal, GroupDealProduct
from models.order import Order, OrderItem
from models.supplier import Supplier
from models.product_sales_stats import ProductSalesStats
from models.delivery_fee_config import DeliveryFeeConfig
from models.sdr import SDR, CommissionRule, CommissionRecord, QuarterlyBonus
from models.customer_feedback import CustomerFeedback, FeedbackContext, FeedbackOutcome
from models.work_document import WorkDocument, ActionItem

