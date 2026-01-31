"""Admin request/response schemas"""
from marshmallow import Schema, fields, validate, EXCLUDE, ValidationError
from constants.status_enums import OrderStatus, PaymentStatus


class CreateSupplierSchema(Schema):
    """Schema for creating a supplier"""
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    contact_person = fields.String(allow_none=True, validate=validate.Length(max=255))
    phone = fields.String(allow_none=True, validate=validate.Length(max=20))
    email = fields.String(allow_none=True, validate=validate.Email())
    address = fields.String(allow_none=True)
    notes = fields.String(allow_none=True)
    is_active = fields.Boolean(missing=True)
    
    class Meta:
        unknown = EXCLUDE


class UpdateSupplierSchema(Schema):
    """Schema for updating a supplier"""
    name = fields.String(allow_none=True, validate=validate.Length(min=1, max=255))
    contact_person = fields.String(allow_none=True, validate=validate.Length(max=255))
    phone = fields.String(allow_none=True, validate=validate.Length(max=20))
    email = fields.String(allow_none=True, validate=validate.Email())
    address = fields.String(allow_none=True)
    notes = fields.String(allow_none=True)
    is_active = fields.Boolean(allow_none=True)
    
    class Meta:
        unknown = EXCLUDE


class AssignRoleSchema(Schema):
    """Schema for assigning a role to a user"""
    role = fields.String(required=True, validate=validate.OneOf(['admin', 'user']))
    
    class Meta:
        unknown = EXCLUDE


class UpdateOrderStatusSchema(Schema):
    """Schema for updating order status"""
    status = fields.String(required=True, validate=validate.OneOf(OrderStatus.get_all_values()))
    
    class Meta:
        unknown = EXCLUDE


class UpdateOrderPaymentSchema(Schema):
    """Schema for updating order payment status"""
    payment_status = fields.String(required=True, validate=validate.OneOf(PaymentStatus.get_all_values()))
    payment_method = fields.String(allow_none=True, validate=validate.Length(max=50))
    
    class Meta:
        unknown = EXCLUDE


class MergeOrdersSchema(Schema):
    """Schema for merging multiple orders"""
    order_ids = fields.List(fields.Integer(), required=True, validate=validate.Length(min=2))
    keep_payment_method = fields.String(allow_none=True)
    keep_delivery_method = fields.String(allow_none=True)
    keep_address_id = fields.Integer(allow_none=True)
    keep_pickup_location = fields.String(allow_none=True)
    keep_notes = fields.String(allow_none=True)
    
    class Meta:
        unknown = EXCLUDE


class DeliveryFeeTierSchema(Schema):
    """Schema for a single delivery fee tier"""
    threshold = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    fee = fields.Decimal(required=True, places=2, validate=validate.Range(min=0))
    
    class Meta:
        unknown = EXCLUDE


def validate_tiers(tiers):
    """Validate that tiers are in ascending order by threshold"""
    if not tiers or len(tiers) < 1:
        raise ValidationError('At least one tier is required')
    
    # Check if first tier has threshold of 0 (base fee)
    if tiers[0].get('threshold') != 0:
        raise ValidationError('First tier must have threshold of 0 (base fee)')
    
    # Validate ascending order
    for i in range(1, len(tiers)):
        if tiers[i].get('threshold', 0) <= tiers[i-1].get('threshold', 0):
            raise ValidationError('Tiers must be in ascending order by threshold amount')
    
    return True


class UpdateDeliveryFeeConfigSchema(Schema):
    """Schema for updating delivery fee configuration with dynamic tiers"""
    tiers = fields.List(
        fields.Nested(DeliveryFeeTierSchema),
        required=True,
        validate=[validate.Length(min=1), validate_tiers]
    )
    
    class Meta:
        unknown = EXCLUDE


class UpdateUserSchema(Schema):
    """Schema for updating user information (admin only)"""
    phone = fields.String(allow_none=True, validate=validate.Length(max=20))
    nickname = fields.String(allow_none=True, validate=validate.Length(max=255))
    email = fields.String(allow_none=True, validate=validate.Email())
    wechat = fields.String(allow_none=True, validate=validate.Length(max=255))
    points = fields.Integer(allow_none=True, validate=validate.Range(min=0))
    user_source = fields.String(allow_none=True, validate=validate.Length(max=50))
    status = fields.String(allow_none=True, validate=validate.OneOf(['active', 'banned', 'inactive']))
    
    class Meta:
        unknown = EXCLUDE

