"""
Status Enums - Single Source of Truth
All status values and labels for the entire application
"""
from enum import Enum


class OrderStatus(str, Enum):
    """
    Order Status Enum
    Workflow: submitted → confirmed → preparing → ready_for_pickup/out_for_delivery → completed
    Can be cancelled at any stage
    """
    SUBMITTED = 'submitted'           # 已提交订单 - User placed order, can edit/cancel
    CONFIRMED = 'confirmed'           # 已确认订单 - Order deadline passed, user cannot edit
    PREPARING = 'preparing'           # 正在配货 - Admin started preparing
    READY_FOR_PICKUP = 'ready_for_pickup'  # 可以取货 - Ready for customer pickup
    OUT_FOR_DELIVERY = 'out_for_delivery'  # 正在配送 - Out for delivery (delivery orders only)
    COMPLETED = 'completed'           # 订单完成 - Order completed and paid
    CANCELLED = 'cancelled'           # 已取消 - Order cancelled

    @classmethod
    def get_label(cls, status):
        """Get Chinese label for status"""
        labels = {
            cls.SUBMITTED: '已提交订单',
            cls.CONFIRMED: '已确认订单',
            cls.PREPARING: '正在配货',
            cls.READY_FOR_PICKUP: '可以取货',
            cls.OUT_FOR_DELIVERY: '正在配送',
            cls.COMPLETED: '订单完成',
            cls.CANCELLED: '已取消',
        }
        return labels.get(status, status)
    
    @classmethod
    def get_all_values(cls):
        """Get all valid status values"""
        return [status.value for status in cls]
    
    @classmethod
    def get_all_labels(cls):
        """Get all status values with labels"""
        return {status.value: cls.get_label(status) for status in cls}
    
    @classmethod
    def is_editable_by_user(cls, status):
        """Check if user can edit order in this status"""
        return status == cls.SUBMITTED
    
    @classmethod
    def is_cancellable_by_user(cls, status):
        """Check if user can cancel order in this status"""
        return status == cls.SUBMITTED


class PaymentStatus(str, Enum):
    """
    Payment Status Enum
    """
    UNPAID = 'unpaid'  # 未付款
    PAID = 'paid'      # 已付款

    @classmethod
    def get_label(cls, status):
        """Get Chinese label for status"""
        labels = {
            cls.UNPAID: '未付款',
            cls.PAID: '已付款',
        }
        return labels.get(status, status)
    
    @classmethod
    def get_all_values(cls):
        """Get all valid status values"""
        return [status.value for status in cls]
    
    @classmethod
    def get_all_labels(cls):
        """Get all status values with labels"""
        return {status.value: cls.get_label(status) for status in cls}


class GroupDealStatus(str, Enum):
    """
    Group Deal Status Enum
    Auto-managed: upcoming → active → closed (by cron job based on dates)
    Manual: preparing → ready_for_pickup → completed (by admin)
    """
    UPCOMING = 'upcoming'             # 即将开始 - Before order_start_date (auto)
    ACTIVE = 'active'                 # 进行中 - Between order dates (auto)
    CLOSED = 'closed'                 # 已截单 - After order_end_date (auto)
    PREPARING = 'preparing'           # 正在配货 - Admin started preparing (manual)
    READY_FOR_PICKUP = 'ready_for_pickup'  # 可以取货 - Ready for pickup (manual)
    COMPLETED = 'completed'           # 已完成 - All done (manual)

    @classmethod
    def get_label(cls, status):
        """Get Chinese label for status"""
        labels = {
            cls.UPCOMING: '即将开始',
            cls.ACTIVE: '进行中',
            cls.CLOSED: '已截单',
            cls.PREPARING: '正在配货',
            cls.READY_FOR_PICKUP: '可以取货',
            cls.COMPLETED: '已完成',
        }
        return labels.get(status, status)
    
    @classmethod
    def get_all_values(cls):
        """Get all valid status values"""
        return [status.value for status in cls]
    
    @classmethod
    def get_all_labels(cls):
        """Get all status values with labels"""
        return {status.value: cls.get_label(status) for status in cls}
    
    @classmethod
    def is_auto_managed(cls, status):
        """Check if status is auto-managed by system"""
        return status in [cls.UPCOMING, cls.ACTIVE, cls.CLOSED]
    
    @classmethod
    def is_manual_managed(cls, status):
        """Check if status is manually managed by admin"""
        return status in [cls.PREPARING, cls.READY_FOR_PICKUP, cls.COMPLETED]
    
    @classmethod
    def get_auto_managed_statuses(cls):
        """Get list of auto-managed statuses"""
        return [cls.UPCOMING.value, cls.ACTIVE.value, cls.CLOSED.value]
    
    @classmethod
    def get_manual_managed_statuses(cls):
        """Get list of manually managed statuses"""
        return [cls.PREPARING.value, cls.READY_FOR_PICKUP.value, cls.COMPLETED.value]


class UserStatus(str, Enum):
    """
    User Status Enum
    """
    ACTIVE = 'active'   # 活跃用户
    BANNED = 'banned'   # 已禁用

    @classmethod
    def get_label(cls, status):
        """Get Chinese label for status"""
        labels = {
            cls.ACTIVE: '活跃',
            cls.BANNED: '已禁用',
        }
        return labels.get(status, status)
    
    @classmethod
    def get_all_values(cls):
        """Get all valid status values"""
        return [status.value for status in cls]
    
    @classmethod
    def get_all_labels(cls):
        """Get all status values with labels"""
        return {status.value: cls.get_label(status) for status in cls}


class DeliveryMethod(str, Enum):
    """
    Delivery Method Enum
    """
    PICKUP = 'pickup'      # 自取
    DELIVERY = 'delivery'  # 配送

    @classmethod
    def get_label(cls, method):
        """Get Chinese label for delivery method"""
        labels = {
            cls.PICKUP: '自取',
            cls.DELIVERY: '配送',
        }
        return labels.get(method, method)
    
    @classmethod
    def get_all_values(cls):
        """Get all valid delivery methods"""
        return [method.value for method in cls]
    
    @classmethod
    def get_all_labels(cls):
        """Get all delivery methods with labels"""
        return {method.value: cls.get_label(method) for method in cls}


class PaymentMethod(str, Enum):
    """
    Payment Method Enum
    """
    CASH = 'cash'          # 现金
    ETRANSFER = 'etransfer'  # 电子转账

    @classmethod
    def get_label(cls, method):
        """Get Chinese label for payment method"""
        labels = {
            cls.CASH: '现金',
            cls.ETRANSFER: '电子转账',
        }
        return labels.get(method, method)
    
    @classmethod
    def get_all_values(cls):
        """Get all valid payment methods"""
        return [method.value for method in cls]
    
    @classmethod
    def get_all_labels(cls):
        """Get all payment methods with labels"""
        return {method.value: cls.get_label(method) for method in cls}


# Export for easy access
__all__ = ['OrderStatus', 'PaymentStatus', 'GroupDealStatus', 'UserStatus', 'DeliveryMethod', 'PaymentMethod']

